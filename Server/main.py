import re
import random
import uuid
import urllib
from flask import Flask, session, request, render_template, Response, send_file, make_response
import csv
import zipfile
import json
import os
from time import sleep

app = Flask(__name__)
random.seed(uuid.getnode())
app.config['SECRET_KEY'] = str(random.random()*233)
app.debug = True

upload_path = "BaiduSearch_Spider/keyword/"
filename = "keywords.csv"


@app.route('/')
def index():
    session['username'] = 'www-data'
    return render_template("index.html", title="百度信息榨取")


@app.route('/multi_keyword')
def multi_keyword():
    return render_template("multi_keyword.html", title="百度信息榨取")


# 读取csv并且输入为json
def read_csv(filename,spider='search'):
    csvfile = open(filename,encoding='utf-8-sig')
    if spider == 'search':
        header = ('title', 'time', 'brief', 'link')
    else:
        header = ('title','platform','date','time','brief','body','link')
    reader = csv.DictReader(csvfile, header)
    result = []
    for row in reader:
        result.append(json.dumps(row))
    return result


# 输入关键词搜索的爬虫
@app.route('/api/search_spider', methods=['GET', 'POST'])
def search_spider():
    keyword = request.args.get("keyword")
    os.system(
        'scrapy crawl searchspider -a search="{}" -a keyword="{}"'.format(keyword, keyword))
    # 打印前10条
    result = read_csv('BaiduSearch_Spider\data\\searchdata\\baidu_{}.csv'.format(keyword.replace("|"," ")),'search')[1:21]
    data = '[' + ','.join(result) + ']'
    res = {
        'code': 0,
        'msg': 'success',
        'count': len(result),
        'data': json.loads(data)
    }
    return Response(json.dumps(res), content_type='application/json')


@app.route('/api/news_spider', methods=['GET', 'POST'])
def news_spider():
    keyword = request.args.get("keyword")
    os.system(
        'scrapy crawl newsspider -a search="{}" -a keyword="{}"'.format(keyword, keyword))
    # 打印前20条
    result = read_csv('BaiduSearch_Spider\data\\newsdata\\baidu_{}.csv'.format(keyword.replace("|"," ")),'news')[1:21]
    data = '[' + ','.join(result) + ']'
    res = {
        'code': 0,
        'msg': 'success',
        'count': len(result),
        'data': json.loads(data)
    }
    return Response(json.dumps(res), content_type='application/json')



@app.route('/api/download_files', methods=['GET','POST'])
def download_files():
    typ = request.args.get("type")
    if typ == "search":
        output_path = "BaiduSearch_Spider\data\\searchdata"
        file_name = 'baidu_search.csv'
    else:
        output_path = "BaiduSearch_Spider\data\\newsdata"
        file_name = 'baidu_news.csv'
    with zipfile.ZipFile('result.zip','w') as target:
        for i in os.walk(output_path):
            print(i)
            for n in i[2]:
                target.write(''.join((i[0],'\\',n)),n)
        target.close()
    file_name = "result.zip"
    res = make_response(
        send_file("../" + file_name))
    res.headers['Content-Disposition'] = 'attachment; filename={}'.format(
        file_name)
    return res

@app.route('/api/download')
def download():
    typ = request.args.get("type")
    if typ == "search":
        output_path = "..\\BaiduSearch_Spider\data\\searchdata"
        file_name = 'baidu_search.csv'
    else:
        output_path = "..\\BaiduSearch_Spider\data\\newsdata"
        file_name = 'baidu_news.csv'
    res = make_response(
        send_file(os.path.join(output_path,file_name)))
    res.headers['Content-Disposition'] = 'attachment; filename={}'.format(
        'result.csv')
    return res


@app.route('/api/check_status',methods=['GET','POST'])
def check_status():
    typ = request.args.get("type")
    if typ == "search":
        output_path = "BaiduSearch_Spider\data\\searchdata"
    else:
        output_path = "BaiduSearch_Spider\data\\newsdata"
    count = len(os.listdir(output_path))
    res = {
        'count' : count,
        'code' : 0,
        'msg' : 'success'
    }
    return Response(json.dumps(res), content_type='application/json')


# 从csv文件中读取关键词爬取
@app.route('/api/file_spider', methods=['GET', 'POST'])
def file_spider():
    # 获取关键词的总数量
    count = len(open(upload_path + filename,encoding='utf-8-sig').readlines())
    # 进行爬虫操作，由于文件比较大一般不可能等到爬完，所以新建一个线程进行爬取
    typ = request.args.get("type")
    if typ == "search":
        os.popen("scrapy crawl searchspider")
    else:
        os.popen("scrapy crawl newsspider")
    res = {
        "count" : count,
        "code" : 0,
        'msg': 'success'
    }
    return Response(json.dumps(res), content_type='application/json')


@app.route('/api/upload', methods=['GET', 'POST'])
def upload():
    # print(request.)
    try:
        file = request.files['file']
        file.save(upload_path + filename)
        res = {
            'code': 0,
            'msg': 'Upload success'
        }
    except:
        res = {
            'code': 1,
            'msg': 'Upload failed'
        }
    return Response(json.dumps(res), content_type='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
