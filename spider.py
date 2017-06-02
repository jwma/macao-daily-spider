# coding=utf-8
from urllib.request import urlopen
import time
import json
import sys

url = 'https://h5.newaircloud.com/api/getLayouts?sid=aomen&cid=10038&date='
full_list_response = urlopen(url)
list_data = json.loads(full_list_response.read().decode('utf8'))
full_list_response.close()

layouts = list_data.get('layouts')

if layouts is None:
    print('返回的数据没有版面数据，请手动检查接口数据是否正确。')
    sys.exit()

for layout in layouts:
    layout_name = layout.get('name')

    if layout_name is None:
        print('版面名称不存在，跳过。')
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

        news_data_response = urlopen(news_data_url)
        news_data_str = news_data_response.read().decode('utf8')
        news_data_response.close()

        print('%s | %s' % (layout_name, layout_date))
        print(news_data_url)
        news_data = eval(news_data_str.strip('var gArticleJson = '),
                         type('Dummy', (dict,), dict(__getitem__=lambda s, n: n))())
        print(news_data)
        print('')

        time.sleep(0.3)

    time.sleep(1)
