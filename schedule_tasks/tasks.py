import time
import json
from apps.ncov.ncov_crawler import Crawler
from apps.ncov.predict import predict
from datetime import datetime, date, timedelta
from apps.mongo_client import nCovCasesDXYDB
from schedule_tasks.logger import logger


nCoV_dxy = nCovCasesDXYDB()
today = datetime.now().date()


class CJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


def crawl_dxy():
    logger.info("抓取丁香园")
    yesterday = (date.today() + timedelta(days=-1)).strftime('%m.%d')

    crawler = Crawler()

    # overall, area = crawler.crawler(True)
    count = 0
    overall, area = {}, {}
    while count < 20:
        overall, area = crawler.crawler(crawl=True)
        if overall:
            logger.info('抓取成功')
            break
        time.sleep(3)
        logger.error('失败重试')
        count += 1

    yesterday_data = nCoV_dxy.find_one({'date': yesterday})

    if overall and area:
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

            hubei_confirm = area[0]['confirmedCount']
            nohubei_confirm = sum([i['confirmedCount'] for i in area[1:]])
            nohuei_cureCount = sum([i['curedCount'] for i in area[1:]])
            nohuei_cureIncr = sum([i['curedAddCount'] for i in area[1:]])
            data = {}
            data['overall'] = overall
            data['overall_new'] = overall
            data['area'] = area
            data['hubei_confirm'] = hubei_confirm
            data['nohubei_confirm'] = nohubei_confirm
            data['nohubei_cureCount'] = nohuei_cureCount
            data['nohubei_cureIncr'] = nohuei_cureIncr
            data['hubei_cureCount'] = area[0]['curedCount']
            data['hubei_cureIncr'] = area[0]['curedAddCount']
            data['date'] = datetime.now().strftime('%m.%d')
            data['save_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['source'] = 'dxy'
            exists = nCoV_dxy.find_one({'date': datetime.now().strftime('%m.%d')})
            if exists:
                if 'overall_new' in data:
                    data.pop('overall_new')
                nCoV_dxy.update_one({'date': datetime.now().strftime('%m.%d')}, {'$set': data})
            else:
                nCoV_dxy.insert_one(data)

        logger.info("丁香园抓取完成")


def update_overall_timed():
    logger.info("更新实时数据")
    crawler = Crawler()
    count = 0
    overall, area = {}, {}
    while count < 20:
        overall, area = crawler.crawler(crawl=True)
        if overall:
            logger.info('抓取成功')
            break
        time.sleep(3)
        logger.error('失败重试')
        count += 1
    today = datetime.now().strftime('%m.%d')
    t_data = nCoV_dxy.find_one({'date': today})

    if overall and area and t_data:
        if 'area' in t_data:
            province_dic = {}
            cities_dic = {}
            for ya in t_data['area']:
                province_dic[ya['provinceName']] = ya
                for yc in ya['cities']:
                    cities_dic[f"{ya['provinceName']}_{yc['cityName']}"] = yc
            if province_dic and cities_dic:
                for ta in area:
                    if ta['provinceName'] in province_dic:
                        ta['confirmedAddCount'] = province_dic[ta['provinceName']]['confirmedAddCount']
                        ta['suspectedAddCount'] = province_dic[ta['provinceName']]['suspectedAddCount']
                        ta['curedAddCount'] = province_dic[ta['provinceName']]['curedAddCount']
                        ta['deadAddCount'] = province_dic[ta['provinceName']]['deadAddCount']
                        for tc in ta['cities']:
                            if f"{ta['provinceName']}_{tc['cityName']}" in cities_dic:
                                tc['confirmedAddCount'] = cities_dic[f"{ta['provinceName']}_{tc['cityName']}"].get('confirmedAddCount', '')
                                tc['suspectedAddCount'] = cities_dic[f"{ta['provinceName']}_{tc['cityName']}"].get('suspectedAddCount', '')
                                tc['curedAddCount'] = cities_dic[f"{ta['provinceName']}_{tc['cityName']}"].get('curedAddCount', '')
                                tc['deadAddCount'] =cities_dic[f"{ta['provinceName']}_{tc['cityName']}"].get('deadAddCount', '')
        nCoV_dxy.update_one({'date': today}, {'$set': {'overall_new': overall, 'area_new': area}})
    elif overall and area and not t_data:
        nCoV_dxy.insert_one({'date': today, 'overall_new': overall, 'area_new': area})

    logger.info('实时数据更新完成')


def save_predict_history():
    logger.info('开始保存预测记录')
    data = predict()
    data.pop('world')
    dic = {}
    for area, results in data.items():
        for r in results:
            r['area'] = area
            if r['date'] in dic:
                dic[r['date']].append(r)
            else:
                dic[r['date']] = [r]

    insert_data = {}
    for date, ret in dic.items():
        items = {}
        for i in ret:
            area = i.pop('area')
            items[area] = i
        insert_data[date] = items

    for k, v in insert_data.items():
        if k == today:
            forcast_result = json.dumps(v, ensure_ascii=False, cls=CJsonEncoder)
            nCoV_dxy.update_one({'date': today.strftime('%m.%d')},
                                {'$set': {'forcast_result': json.loads(forcast_result)}})
            logger.info('保存历史预测完成')
            break


def save_predict_history_remedial():
    '''
    当前一天的历史记录保存失败时
    :return:
    '''
    import requests
    res = requests.get('https://innovaapi.aminer.cn/covid/api/v1/pneumonia/prediction')
    # with open('prediction.json', 'w') as f:
    #     f.write(res.text)
    logger.info('开始保存预测记录')
    data = res.json()['data']
    data.pop('world')
    dic = {}
    for area, results in data.items():
        for r in results:
            r['area'] = area
            if r['date'] in dic:
                dic[r['date']].append(r)
            else:
                dic[r['date']] = [r]

    insert_data = {}
    for date, ret in dic.items():
        items = {}
        for i in ret:
            area = i.pop('area')
            items[area] = i
        insert_data[date] = items
    insert_time = today + timedelta(days=-1)
    insert_time_str = insert_time.strftime('%Y-%m-%d')
    for k, v in insert_data.items():
        if k <= insert_time_str:
            if nCoV_dxy.find_one({'date': '.'.join(k.split('-')[1:]), 'forcast_result': {'$exists': False}}):
                print(k)
                forcast_result = json.dumps(v, ensure_ascii=False, cls=CJsonEncoder)
                print(forcast_result)
                nCoV_dxy.update_one({'date': '.'.join(k.split('-')[1:])},
                                    {'$set': {'forcast_result': json.loads(forcast_result)}})
                logger.info('保存历史预测完成')


if __name__ == '__main__':
    opt = 4
    if opt == 1:
        update_overall_timed()
    elif opt == 2:
        crawl_dxy()
    elif opt == 3:
        save_predict_history()
    elif opt == 4:
        save_predict_history_remedial()