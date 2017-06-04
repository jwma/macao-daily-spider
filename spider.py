# coding=utf-8
from urllib.request import urlopen, urlretrieve
import time
import json
import sys
import os

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

for layout in layouts:
    layout_name = layout.get('name')

    if layout_name is None:
        print('版面名称不存在，跳过')
        continue

    layout_date = layout.get('date')
    layout_pic_url = layout.get('picUrl')
    news_list = layout.get('list')

    if news_list is None:
        print('%s 没有新闻列表，跳过' % layout_name)
        continue

    for news in news_list:
        news_id = news.get('id')
        news_title = news.get('title')
        news_pic = news.get('pic1')
        news_data_url = news.get('curl')

        print('当前：%s | %s' % (layout_name, layout_date))
        print(news_data_url)

        urlretrieve(news_data_url, '%s/%s.js' % (new_tmp_data_path, news_id))
        time.sleep(0.1)

    time.sleep(0.3)

print('数据抓取完成')
