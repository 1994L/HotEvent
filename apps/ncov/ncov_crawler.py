"""
@ProjectName: DXY-2019-nCov-Crawler
@FileName: crawler.py
@Author: Jiabao Lin
@Date: 2020/1/21
"""
from bs4 import BeautifulSoup
import re
import json
import time
import datetime
import random
import requests
from apps.mongo_client import nCovCasesDB, nCovCasesDXYDB
from utils.decorators import timing
from datetime import date, timedelta
from utils.logger import logRecord


nCoV_dxy = nCovCasesDXYDB()

country_type = {
    1: '中国'
}


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5"
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
]

# headers = {
#     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
# }


class Crawler:
    def __init__(self):
        # self.session = requests.session()
        # self.session.headers.update(headers)
        self.crawl_timestamp = int()

    def run(self):
        while True:
            self.crawler()
            time.sleep(60)

    def cal_newadd(self, area):
        yesterday = (date.today() + timedelta(days=-1)).strftime('%m.%d')
        yesterday_data = nCoV_dxy.find_one({'date': yesterday})
        province_dic = {}
        cities_dic = {}
        if yesterday_data:
            yesterday_area = yesterday_data['area']
            for ya in yesterday_area:
                province_dic[ya['provinceName']] = ya
                for yc in ya['cities']:
                    cities_dic[f"{ya['provinceName']}_{yc['cityName']}"] = yc

        if province_dic and cities_dic:
            for ta in area:
                if ta['provinceName'] in province_dic:
                    ta['confirmedAddCount'] = ta['confirmedCount'] - province_dic[ta['provinceName']]['confirmedCount']
                    ta['suspectedAddCount'] = ta['suspectedCount'] - province_dic[ta['provinceName']]['suspectedCount']
                    ta['curedAddCount'] = ta['curedCount'] - province_dic[ta['provinceName']]['curedCount']
                    ta['deadAddCount'] = ta['deadCount'] - province_dic[ta['provinceName']]['deadCount']
                    for tc in ta['cities']:
                        if f"{ta['provinceName']}_{tc['cityName']}" in cities_dic:
                            tc['confirmedAddCount'] = tc['confirmedCount'] - \
                                                      cities_dic[f"{ta['provinceName']}_{tc['cityName']}"][
                                                          'confirmedCount']
                            tc['suspectedAddCount'] = tc['suspectedCount'] - \
                                                      cities_dic[f"{ta['provinceName']}_{tc['cityName']}"][
                                                          'suspectedCount']
                            tc['curedAddCount'] = tc['curedCount'] - \
                                                  cities_dic[f"{ta['provinceName']}_{tc['cityName']}"]['curedCount']
                            tc['deadAddCount'] = tc['deadCount'] - cities_dic[f"{ta['provinceName']}_{tc['cityName']}"][
                                'deadCount']
        return area

    @timing
    def crawler(self, crawl=False):
        if not crawl:
            today = datetime.datetime.now().strftime('%m.%d')
            data = nCoV_dxy.find_one({'date': today})
            if data:
                logRecord('overall and area from db')
                return data['overall_new'], data['area_new']


        overall, area, abroad = {}, {}, {}
        count = 0
        while True:
            if count == 20:
                break

            self.crawl_timestamp = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
            try:
                headers = {
                    'user-agent': random.choice(USER_AGENTS)
                }
                # r = self.session.get(url='https://3g.dxy.cn/newh5/view/pneumonia', timeout=10)
                r = requests.get(url='https://3g.dxy.cn/newh5/view/pneumonia', headers=headers, timeout=10)
            except Exception as e:
                count += 1
                time.sleep(1)
                logRecord('请求链接: https://3g.dxy.cn/newh5/view/pneumonia 失败', 'error')
                continue
            soup = BeautifulSoup(r.content, 'html.parser')

            overall_information = re.search(r'\{("id".*?)\}\}', str(soup.find('script', attrs={'id': 'getStatisticsService'})))
            # province_information = re.search(r'\[(.*?)\]', str(soup.find('script', attrs={'id': 'getListByCountryTypeService1'})))
            area_information = re.search(r'\[(.*)\]', str(soup.find('script', attrs={'id': 'getAreaStat'})))
            # abroad_information = re.search(r'\[(.*)\]', str(soup.find('script', attrs={'id': 'getListByCountryTypeService2'})))
            # news = re.search(r'\[(.*?)\]', str(soup.find('script', attrs={'id': 'getTimelineService'})))
            if not overall_information or not area_information:
                count += 1
                print('dxy没抓到')
                time.sleep(2)
                continue
            # if not overall_information and not area_information:
            #     count += 1
            #     continue

            if overall_information:
                overall = self.overall_parser(overall_information=overall_information)
            # self.province_parser(province_information=province_information)
            if area_information:
                area = self.area_parser(area_information=area_information)
            # abroad = self.abroad_parser(abroad_information=abroad_information)
            # self.news_parser(news=news)

            break

        # while True:
        #     self.crawl_timestamp = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        #     try:
        #         r = self.session.get(url='https://file1.dxycdn.com/2020/0127/797/3393185293879908067-115.json')
        #     except requests.exceptions.ChunkedEncodingError:
        #         continue
        #     # Use try-except to ensure the .json() method will not raise exception.
        #     try:
        #         if r.status_code != 200:
        #             continue
        #         elif r.json().get('code') == 'success':
        #             self.rumor_parser(rumors=r.json().get('data'))
        #             break
        #         else:
        #             continue
        #     except json.decoder.JSONDecodeError:
        #         continue

        logRecord('Successfully crawled.')
        return overall, area

    def overall_parser(self, overall_information):
        # print(overall_information.group(0))
        overall_information = json.loads(overall_information.group(0)[:-1])
        overall_information.pop('id')
        overall_information.pop('createTime')
        overall_information.pop('modifyTime')
        overall_information.pop('imgUrl')
        overall_information.pop('deleted')
        overall_information.pop('infectSource')
        overall_information.pop('passWay')
        overall_information.pop('marquee')
        overall_information.pop('dailyPic')
        overall_information.pop('virus')

        overall_information['countRemark'] = overall_information['countRemark'].replace(' 疑似', '，疑似').replace(' 治愈', '，治愈').replace(' 死亡', '，死亡').replace(' ', '')
        # if not self.db.find_one(collection='DXYOverall', data=overall_information):
        #     overall_information['updateTime'] = self.crawl_timestamp
        #
        #     self.db.insert(collection='DXYOverall', data=overall_information)
        return overall_information

    def province_parser(self, province_information):
        provinces = json.loads(province_information.group(0))
        for province in provinces:
            province.pop('id')
            province.pop('tags')
            province.pop('sort')
            province['comment'] = province['comment'].replace(' ', '')
            # if self.db.find_one(collection='DXYProvince', data=province):
            #     continue
            province['crawlTime'] = self.crawl_timestamp
            province['country'] = country_type.get(province['countryType'])

            # self.db.insert(collection='DXYProvince', data=province)
        print(provinces)

    def area_parser(self, area_information):
        area_information = json.loads(area_information.group(0))
        for area in area_information:
            area['comment'] = area['comment'].replace(' ', '')
            # if self.db.find_one(collection='DXYArea', data=area):
            #     continue
            area['country'] = '中国'
            area['updateTime'] = self.crawl_timestamp

            # self.db.insert(collection='DXYArea', data=area)
        return area_information

    def abroad_parser(self, abroad_information):
        countries = json.loads(abroad_information.group(0))
        for country in countries:
            country.pop('id')
            country.pop('tags')
            country.pop('countryType')
            country.pop('provinceId')
            country['country'] = country.get('provinceName')
            country['provinceShortName'] = country.get('provinceName')
            country.pop('cityName')
            country.pop('sort')

            country['comment'] = country['comment'].replace(' ', '')
            # if self.db.find_one(collection='DXYArea', data=country):
            #     continue
            country['updateTime'] = self.crawl_timestamp

            # self.db.insert(collection='DXYArea', data=country)
        return countries

    def news_parser(self, news):
        news = json.loads(news.group(0))
        for _news in news:
            _news.pop('pubDateStr')
            # if self.db.find_one(collection='DXYNews', data=_news):
            #     continue
            _news['crawlTime'] = self.crawl_timestamp

            # self.db.insert(collection='DXYNews', data=_news)

    def rumor_parser(self, rumors):
        for rumor in rumors:
            rumor.pop('score')
            rumor['body'] = rumor['body'].replace(' ', '')
            # if self.db.find_one(collection='DXYRumors', data=rumor):
            #     continue
            rumor['crawlTime'] = self.crawl_timestamp

            # self.db.insert(collection='DXYRumors', data=rumor)


if __name__ == '__main__':
    crawler = Crawler()
    ret = crawler.crawler(True)
    print(ret)
