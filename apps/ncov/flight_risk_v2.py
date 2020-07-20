# -*- coding: utf-8 -*-
# @Time    : 2020/3/18 11:17 AM
# @Author  : Bing_Lun
# @Email   :  bing.lun@aminer.cn
# @File    : test4.py
# @Software : PyCharm

import jieba
import requests
import json
import os
# from translate import Translator
import pandas as pd
from datetime import datetime
from apps.ncov.interface import ncov_china
from apps.crawler.crawl_flight import FlightInfo


def get_city_num(cityname):  # 国内疫情数据获取
    if cityname in ['北京', '天津', '上海', '重庆', '香港', '台湾', '澳门']:
        # url="https://innovaapi.aminer.cn/covid/api/v1/pneumonia/data"
        # r = requests.get(url)
        # result=json.loads(r.text).get('data').get('area')
        result = ncov_china().get('area')
        for province in result:
            if province.get('provinceShortName') == cityname:
                return province.get('confirmedCount') - province.get('curedCount') - province.get('deadCount')

    else:
        url = "http://www.dzyong.top:3005/yiqing/area"
        r = requests.get(url)
        result = json.loads(r.text).get('data')
        for citynum in result:
            if citynum.get('cityName') == cityname:
                return citynum.get('confirmedCount') - citynum.get('curedCount') - citynum.get('deadCount')


def get_world_num(countryname):  # 世界疫情数据获取
    url = "https://api.yonyoucloud.com/apis/dst/ncov/wholeworld"
    headers = {"authoration": "apicode", "apicode": "300cf97d07d44c6da8c20380161fa5c9"}
    r = requests.get(url, headers=headers)
    # ,headers={"authoration":"apicode","apicode":"300cf97d07d44c6da8c20380161fa5c9"}
    result = json.loads(r.text).get('data').get('continent')
    try:
        for continent in result:
            for province in continent.get('country'):
                if province.get('provinceName') == countryname:
                    return (province.get('confirmedCount') - province.get('curedCount') - province.get('deadCount'))
    except:
        return 0


def city_to_country_and_num(city):  # 输入是机场名称,返回城市或国家及其对应数量
    world_city_path = os.path.join(os.path.dirname(__file__), 'word_city.xlsx')
    word_country_city = pd.read_excel(world_city_path)
    df = word_country_city
    a = df[(df.city == city)]
    if a.size == 0:
        return 0, 0
    #    if type(get_migration([city], "i"))==str:
    #        return 0,0
    else:
        #        country_ = get_migration([city], "i").get('administrative_division').get('country')
        country = a['country'].values[0]
        if country == '中国':
            #            plan = jieba.cut(city)
            #            cityorcounty = ' '.join(plan).split(' ')[0]
            city_num = get_city_num(city)
            if city_num == None:
                city_num = 0
            return city, city_num

        else:
            #            translator= Translator(to_lang="chinese")
            #            cityorcounty = get_migration([city], "i").get('administrative_division')['en0']
            #            cityorcounty = translator.translate( cityorcounty)
            city_num = get_world_num(country)
            if city_num == None:
                city_num = 0
            return country, city_num


def get_city(figthNo, date):  # 获得航班往返城市
    # r = requests.get("https://innovaapi.aminer.cn/covid/api/v1/flight?flynum=%s&flydate=%s" % (figthNo, date))
    # result = json.loads(r.text).get('data')
    result = FlightInfo(figthNo, date).crawl()
    if result == {} or result == None:
        return 1, 2, 3, 4, 5, 6
    else:
        depcity_cut = jieba.cut(result['origin'])
        depcity_name = ' '.join(depcity_cut).split(' ')[0]
        arrcity_cut = jieba.cut(result['destination'])
        arrcity_name = ' '.join(arrcity_cut).split(' ')[0]
        dplan, dplan_num = city_to_country_and_num(depcity_name)  ##获得出发国家，如果中国则获得城市，别国则获得国家
        aplan, aplan_num = city_to_country_and_num(arrcity_name)  ##获得到达国家，如果中国则获得城市，别国则获得国家
        return dplan, depcity_name, dplan_num, aplan, arrcity_name, aplan_num


def probability_pred(depCity_num, arrCity_num, depCity_weight, arrCity_weight):  # 感染风险预测模型
    if depCity_num == 0 and arrCity_num == 0:
        arrCity_num += 1
    probability = (depCity_weight * depCity_num + arrCity_weight * arrCity_num) / (depCity_num + arrCity_num)  # 定义模型
    return round(probability, 3)


def get_weight(num, city):  # 权重博判断
    '''

    :param num: 该国家或城市的现存确诊人数或新增人数
    :param city: 国家或城市名称
    :return: 得到数量和权重
    '''
    country_list = ['英国', '美国', '瑞典', '瑞士', '日本']  # 不进行数据统计的国家，应该增加其权重
    weight = 0.0
    if city in country_list:
        weight = 0.8
    else:
        if num < 500:
            weight = 0.1
        elif num <= 1000:
            weight = 0.3
        elif num <= 1500:
            weight = 0.5
        else:
            weight = 0.7
    return weight


def flight_risk(figthNo: str, area: str):
    if figthNo:
        date = datetime.now().strftime('%Y%m%d')
        (depCity, depCity2, depCity_num, arrCity, arrCity2, arrCity_num) = get_city(figthNo,
                                                                                    date)  # 获得出发和到达国家，如果中国则获得城市，别国则获得国家
        if not (depCity == 1 and depCity_num == 3 and arrCity == 4 and arrCity_num == 6):
            depCity_weight = get_weight(depCity_num, depCity)
            arrCity_weight = get_weight(arrCity_num, arrCity)
            risk = probability_pred(depCity_num, arrCity_num, depCity_weight, arrCity_weight)
            print('出发地点：%s，到达地点：%s，风险指数：%s' % (depCity2, arrCity2, risk))
            return depCity2, arrCity2, risk
    elif area:
        print(area)
        areaorcounty, area_num = city_to_country_and_num(area)
        print(areaorcounty, area_num)
        if not (areaorcounty == 0 and area_num == 0):
            return get_weight(area_num, areaorcounty)
    print('航班或地点暂未收录或不存在')
    return None


if __name__ == "__main__":
    print("航班查询请输入：1，地点查询请输入：2")
    inquiry_mode = input("请输入1或2：")
    if inquiry_mode == '1':
        figthNo = input("输入航班号:")
        date = '20200320'
        #        date=input('请输入日期：')
        (depCity, depCity2, depCity_num, arrCity, arrCity2, arrCity_num) = get_city(figthNo,
                                                                                    date)  # 获得出发和到达国家，如果中国则获得城市，别国则获得国家
        if depCity == 1 and depCity_num == 3 and arrCity == 4 and arrCity_num == 6:
            print('此航班不存在或暂未收录')
        else:
            depCity_weight = get_weight(depCity_num, depCity)
            arrCity_weight = get_weight(arrCity_num, arrCity)
            print('出发地点：%s，到达地点：%s，风险指数：%s' % (
            depCity2, arrCity2, probability_pred(depCity_num, arrCity_num, depCity_weight, arrCity_weight)))
    elif inquiry_mode == '2':
        area = input('请输入地点：')
        areaorcounty, area_num = city_to_country_and_num(area)
        if areaorcounty == 0 and area_num == 0:
            print('地点暂未收录或不存在')
        else:
            print('风险指数：%s' % get_weight(area_num, areaorcounty))
    else:
        print('您的输入方式不正确')
