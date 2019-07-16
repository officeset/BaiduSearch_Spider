# -*- coding: utf-8 -*-
import scrapy
from BaiduSearch_Spider.items import BaidunewsSpiderItem

from time import sleep
from BaiduSearch_Spider.body_path import path_list

import csv
import os

import urllib


class BaiduspiderSpider(scrapy.Spider):
    name = 'newsspider'
    # allowed_domains = ['http://news.baidu.com/']

    def __init__(self):
        self.ReadKeyword() # 读取关键词

    def ReadKeyword(self): # 设置要包含要搜索关键词的csv文件
        #关键词csv文件的位置
        filename = "高校学生自杀搜索关键词(1).csv"
        path1 = os.path.dirname(__file__)# 获取当前文件所在文件夹
        path2 = os.path.dirname(path1) + '\\keyword\\'+filename# 获取当前文件所在文件夹的父文件夹
        #打开(创建)文件
        file = open(path2,'r',newline='',encoding='utf-8-sig') # 不带newline的话输出总会有一个空行 加入encoding='utf-8-sig'就不会乱码了
        #csv读取
        reader = csv.reader(file) # 建立csv文件句柄
        self.keywords=[]
        for row in reader:
            self.keywords.append(row)
        self.keywords=self.keywords[1:]# 去掉第一项

    def start_requests(self):
        for line in self.keywords:
            line=(line[0]).split()
            keyword="|".join(line)
            begin_page = 0
            end_page = 80
            start_urls1 = "http://news.baidu.com/ns?word={0}&pn={1}&cl=2&ct=0&tn=newsdy&rn=10&ie=utf-8"
            for page in range(begin_page,end_page):# 一页链接数量由参数&rn=决定
                U = start_urls1.format(keyword,page*10)
                yield scrapy.Request(url = U,meta = {'keyword':" ".join(line)},callback = self.parse,dont_filter=False)
            sleep(5)  #设置一个时间间隔，太快了不好
    
    def parse(self,response):
        for section in response.xpath('//div[@class="result" and @id]'):
            item = BaidunewsSpiderItem()
            item['keyword']=response.meta['keyword'] # 标注关键词
            try:
                info = section.xpath('.//a')[0]
                item['link'] = info.xpath('@href').extract()[0]
            except:
                item['link']=""

            try:
                res_title=section.xpath('.//h3/a')
                item['title']=(res_title[0].xpath('string(.)').extract_first()).strip('\n\t \'')
            except:
                item['title']=""
 
            try:
                b=section.xpath('.//div[@class="c-summary c-row " ]')
                if len(b)==0:
                    b=section.xpath('.//div[@class="c-summary c-row c-gap-top-small"]')
                S=b.xpath('string(.)').extract()[0]
                S=S.replace("\n"," ").replace("\t"," ").replace("\xa0"," ")
                List = S.split()
                List.pop() #去除百度快照
                item['platform'] = List[0]
                item['date'] = List[1]
                item['time'] = List[2]
                item['brief'] = "".join(List[3:])
                
            except:
                item['date']=""
                item['platform']=""
                item['brief']=""
                item['time']=""
            yield scrapy.Request(url = item['link'],meta = {'item':item},callback = self.parse_next,dont_filter=True)

    def parse_next(self,response): # 爬取正文的深度只有一层，所以如果正文中有翻页就只能爬取第一页的内容
        item = response.meta['item']
        item['link']=response.url #获取真实的url地址 地址为空则直接返回空的item
        if item['link']=='':
            yield item

        b=[]# 爬取正文的字符串列表
        string="" # 目标正文的字符串
        for path_str in path_list:
            a = response.xpath(path_str)
            if len(a)!=0: # 爬取正文数据 找到了就分析，否则继续寻找
                b=a.xpath('string(.)').extract()
                string="".join(b)
                if len(string)>0: # 爬取到了有用的正文就可以离开循环
                    break
        item['body']=string.replace('\n',"").replace('\t',"").replace(" ","").replace("\r","") # 去除没用的关键字
        yield item 