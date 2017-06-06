# coding=utf-8
from urllib.request import urlopen
import json
import sys
import os
import pymysql.cursors


def crawl_news_url():
    url = 'https://h5.newaircloud.com/api/getLayouts?sid=aomen&cid=10038&date='
    full_list_response = urlopen(url)
    list_data = json.loads(full_list_response.read().decode('utf8'))
    full_list_response.close()

    date = list_data.get('date')
    new_tmp_data_path = './tmp_data/%s' % date
    if not os.path.exists(new_tmp_data_path):
        os.mkdir(new_tmp_data_path)

    layouts = list_data.get('layouts')

    if layouts is None:
        print('返回的数据没有版面数据，请手动检查接口数据是否正确')
        sys.exit()

    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='root',
                                 db='macao_daily',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

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

                # news_data_response = urlopen(news_data_url)
                # news_data_str = news_data_response.read().decode('utf8')
                # news_data_response.close()

                # urlretrieve(news_data_url, '%s/%s.js' % (new_tmp_data_path, news_id))
                # news_data = eval(news_data_str.strip('var gArticleJson = '),
                # type('Dummy', (dict,), dict(__getitem__=lambda s, n: n))())
                # news_data['layout_name'] = layout_name

        connection.commit()

    connection.close()
    print('数据抓取完成')


if __name__ == '__main__':
    actions = ['news_url', 'news_data']

    if len(sys.argv) < 2:
        print('缺少参数，python spider.py %s' % '|'.join(actions))
        exit(1)

    action = sys.argv[1]
    if action == 'news_url':
        crawl_news_url()
    elif action == 'news_data':
        print('待实现')
    else:
        print('不存在的操作，python spider.py %s' % '|'.join(actions))
