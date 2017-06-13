# coding=utf-8
from urllib.request import urlopen, urlretrieve
import json
import sys
import pymysql.cursors
import threading
import time
import os


def get_connection():
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='root',
                                 db='macao_daily',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def crawl_news_url():
    url = 'https://h5.newaircloud.com/api/getLayouts?sid=aomen&cid=10038&date='
    full_list_response = urlopen(url)
    list_data = json.loads(full_list_response.read().decode('utf8'))
    full_list_response.close()

    layouts = list_data.get('layouts')

    if layouts is None:
        print('返回的数据没有版面数据，请手动检查接口数据是否正确')
        sys.exit()

    connection = get_connection()

    for layout in layouts:
        layout_name = layout.get('name')

        if layout_name is None:
            print('版面名称不存在，跳过')
            continue

        layout_date = layout.get('date')
        news_list = layout.get('list')

        if news_list is None:
            print('%s 没有新闻列表，跳过' % layout_name)
            continue

        for news in news_list:
            news_data_url = news.get('curl')

            print('当前：%s | %s' % (layout_name, layout_date))
            print(news_data_url)

            with connection.cursor() as cursor:
                check_sql = 'SELECT COUNT(id) AS `n` FROM `task` WHERE `url` = %s'
                cursor.execute(check_sql, (news_data_url,))
                check_result = cursor.fetchone()
                if check_result.get('n') > 0:
                    print('已存在，跳过')
                    continue

                insert_sql = 'INSERT INTO `task` (`url`, `extra_data`) VALUES (%s, %s)'
                cursor.execute(insert_sql, (news_data_url, json.dumps({'layoutName': layout_name})), )

        connection.commit()

    connection.close()
    print('数据抓取完成')


class TaskWorker(threading.Thread):
    def __init__(self, id, tasks):
        super().__init__()

        self.id = id
        self.tasks = tasks
        self.connection = get_connection()

    def run(self):
        update_task_status_sql = 'UPDATE `task` SET `status` = 1 WHERE `url` = %s'
        insert_news_sql = 'INSERT INTO `news` (`title`, `publishtime`, `content`, `layout`, `layout_name`, `images`)' \
                          ' VALUES (%s, %s, %s, %s, %s, %s)'

        for task in self.tasks:
            news_data_response = urlopen(task['url'])
            news_data = eval(news_data_response.read().decode('utf8').strip('var gArticleJson = '),
                             type('Dummy', (dict,), dict(__getitem__=lambda s, n: n))())
            news_data_response.close()

            title = news_data.get('title')
            publishtime = news_data.get('publishtime')
            content = news_data.get('content')
            layout = news_data.get('layout')
            # images = json.dumps(news_data.get('images'))
            origin_images = news_data.get('images')
            images = []

            if len(origin_images) > 0:
                for i in range(len(origin_images)):
                    image = origin_images[i]
                    save_path = 'images/%s' % os.path.basename(image.get('imageUrl'))
                    urlretrieve(image.get('imageUrl'), save_path)
                    images.append({'summary': image.get('summary'), 'url': save_path})
                    time.sleep(0.01)

            news_extra_data = json.loads(task['extra_data'])
            layout_name = news_extra_data.get('layoutName')

            print('%s - %s' % (self.id, task['url']))
            with self.connection.cursor() as cursor:
                cursor.execute(update_task_status_sql, (task['url'],))
                cursor.execute(insert_news_sql, (title, publishtime, content, layout, layout_name, json.dumps(images),))

            self.connection.commit()
            time.sleep(0.05)

        self.connection.close()
        print('%s 处理完毕' % self.id)


def crawl_news_data():
    connection = get_connection()
    list_task_sql = 'SELECT `url`, `extra_data` FROM `task` WHERE `status` = 0'
    with connection.cursor() as cursor:
        cursor.execute(list_task_sql)
        task_list = cursor.fetchall()
        cursor.close()
        connection.close()

        workers = []
        for i in range(0, len(task_list), 50):
            tasks = task_list[i:i + 50]
            task_worker = TaskWorker(i + 1, tasks)
            task_worker.start()
            workers.append(task_worker)

        for worker in workers:
            worker.join()

        print('全部处理完毕')


if __name__ == '__main__':
    actions = ['news_url', 'news_data']

    if len(sys.argv) < 2:
        print('缺少参数，python spider.py %s' % '|'.join(actions))
        exit(1)

    action = sys.argv[1]
    if action == 'news_url':
        crawl_news_url()
    elif action == 'news_data':
        crawl_news_data()
    else:
        print('不存在的操作，python spider.py %s' % '|'.join(actions))
