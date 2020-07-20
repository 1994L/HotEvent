# -*- coding: utf-8 -*-
# @Time    : 2020/2/10 1:58 PM
# @Author  : Bing_Lun
# @Email   :  bing.lun@aminer.cn
# @File    : main.py
# @Software : PyCharm

import pandas as pd
from pylab import *
mpl.rcParams['font.sans-serif'] = ['SimHei']#解决中文乱码问题
import numpy as np
import os
from dateutil.parser import parse
from utils.decorators import timing
from scipy.optimize import curve_fit
from datetime import datetime, timedelta
from apps.mongo_client import nCovCasesDXYDB, NcovWorldPredictDB
from apps.ncov.interface import nw_col


model_dir_path = os.path.join(os.path.dirname(__file__), 'model')
ncov_dxy = nCovCasesDXYDB()
world_col = NcovWorldPredictDB()
now = datetime.now().strftime('%Y_%m_%d')
today = datetime.now().date()
yesterday = today + timedelta(days=-1)
yes_data = ncov_dxy.find_one({'date': yesterday.strftime('%m.%d')}) or {}
# china_DailyList_path = os.path.join(os.path.dirname(__file__), f'data/china_DailyList_{now}.csv')
model_path = f'{model_dir_path}/model.csv'
nohubei_model_path = f'{model_dir_path}/model_nohubei.csv'
heal_model_path = f'{model_dir_path}/model_heal.csv'
hubei_confirmIncr_model_path = f'{model_dir_path}/model_hubei_confirmIncr.csv'
nohubei_cureIncr_model_path = f'{model_dir_path}/model_nohubeiheal.csv'
hubei_cureIncr_model_path = f'{model_dir_path}/model_hubeiheal.csv'


def logistic_increase_function(t, K, P0, r):
    r = 0.275
    t0 = 1
    exp_value = np.exp(r * (t - t0))
    value = (K * exp_value * P0) / (K + (exp_value - 1) * P0)
    return value

def convert_day_time(num):
    num = str(num)
    if len(num) == 1:
        num = '0' + num
    return num

def date_convert(num):
    if num <= 31:
        return parse(f'202001{convert_day_time(num)}')
    elif 31 < num <= 60:
        return parse(f'202002{convert_day_time(num-31)}')
    elif 60 < num <= 91:
        return parse(f'202003{convert_day_time(num - 60)}')
    elif 91 < num <= 121:
        return parse(f'202004{convert_day_time(num - 91)}')
    elif 121 < num <= 152:
        return parse(f'202005{convert_day_time(num - 121)}')


hyperparameters_r = None


def logistic_increase_function_v2(t, K, P0, r):
    r = hyperparameters_r
    t0 = 11
    # K = 81000
    exp_value = np.exp(r * (t - t0))
    value = (K * exp_value * P0) / (K + (exp_value - 1) * P0)
    return value

@timing
def overall_confirm_predict(pre_days):
    # data = pd.read_csv(china_DailyList_path)

    # data = pd.read_csv('/Users/AMiner/AMiner/Aitools/Predictor/apps/hot_events/pneumonia/data/china_DailyList_2020_02_12.csv')
    ##day_id为已知填出的编码为，1月13日至2月7日，根据之后的情况进行相应的进行增加天数
    data = ncov_dxy.find_many({'overall': {'$exists': True}}).sort([('date', 1)])
    con_value = pd.Series([i['overall']['confirmedCount'] for i in data])
    # con_value = data['confirm']
    day_id = [i + 1 for i in range(len(con_value))]
    day = np.array(day_id)
    con = np.array(con_value)
    popt, pocv = curve_fit(logistic_increase_function, day, con)

    # 第二种预测
    popt_v2 = np.loadtxt(open(model_path), delimiter=",", skiprows=0)
    global hyperparameters_r
    hyperparameters_r = popt_v2[3]

    pre_day = {}
    for i in range(pre_days):

        date_time = date_convert(i + 26).date()
        if date_time >= today:
        # if True:
            ##从1月25日开始进行预测，预测之后60天的变化情况
            # people_sick = int(logistic_increase_function(np.array([i + 12]), popt[0], popt[1], popt[2]))
            ##输出为天数id需要变为真实日期，以及预测人数

            people_sick_v2 = int(logistic_increase_function_v2(np.array([i + 12]), popt_v2[0], popt_v2[1], popt_v2[2]))


            yes_date_time = date_convert(i + 25).date()
            real = ncov_dxy.find_one({'date': date_time.strftime('%m.%d'), 'overall': {'$exists': True}})
            yes_real = ncov_dxy.find_one({'date': yes_date_time.strftime('%m.%d')}) or {}
            if real:
                real_confirm = real.get('overall', {}).get('confirmedCount', 0)
                real_cured = real.get('overall', {}).get('curedCount', 0)
                real_curedIncr = real_cured - yes_real.get('overall', {}).get('curedCount', 0)
                real_curedIncr = real_curedIncr if real_curedIncr >= 0 else 0
            else:
                real_confirm = 0
                real_cured = 0
                real_curedIncr = 0
            pre_day[date_time] = {
                'date': date_time,
                'real': real_confirm,
                'forcast': people_sick_v2,
                'curedCount': real_cured,
                'cureIncr': real_curedIncr
            }
            yes_real_confirm = yes_real.get('overall', {}).get('confirmedCount', 0)
            if yes_real_confirm:
                forcastConfirmedIncr = people_sick_v2 - yes_real.get('overall', {}).get('confirmedCount', 0)
            else:
                forcastConfirmedIncr = people_sick_v2 - int(logistic_increase_function_v2(np.array([i + 11]), popt_v2[0], popt_v2[1], popt_v2[2]))


    return pre_day

def logistic_increase_function_nohubei(t, K, P0, hyperparameters_r):
    r = hyperparameters_r
    t0 = 11
    # K = 49557
    exp_value = np.exp(r * (t - t0))
    value = (K * exp_value * P0) / (K + (exp_value - 1) * P0)
    return value


def nohubei_confirm_predict(pre_days=100):
    popt = np.loadtxt(open(nohubei_model_path), delimiter=",", skiprows=0)
    hyperparameters_r = popt[3]
    pre_day = {}
    for i in range(pre_days):

        date_time = date_convert(i + 20).date()
        if date_time == yesterday:
            yes_confirm = yes_data.get('nohubei_confirm', 0)
        if date_time >= today:
        # if 1:
            day = i + 1
            people_sick = int(logistic_increase_function_nohubei(np.array([day]), popt[4], popt[1], hyperparameters_r))
            yes_people_sick = int(logistic_increase_function_nohubei(np.array([day-1]), popt[4], popt[1], hyperparameters_r))
            '''
            应该输出日期和预测结果
            目前输出的日期id和预测结果
            从1月20日开始计算
            '''

            real = ncov_dxy.find_one({'date': date_time.strftime('%m.%d'), 'overall': {'$exists': True}})
            if real:
                confirmed = real.get('nohubei_confirm', 0)
                cureIncr = real.get('nohubei_cureIncr', 0)
            else:
                confirmed = 0
                cureIncr = 0
            forcastConfirmedIncr = people_sick - yes_people_sick
            pre_day[date_time] = {
                'date': date_time,
                'real': confirmed,
                'forcast': yes_confirm + forcastConfirmedIncr,
                'forcastConfirmedIncr': forcastConfirmedIncr,
                'cureIncr': cureIncr
            }
            yes_confirm += forcastConfirmedIncr
    return pre_day


def heal_convert_date(num):
    if num <= 29:
        return parse(f'202002{convert_day_time(num)}')
    elif 29 < num <= 60:
        return parse(f'202003{convert_day_time(num-29)}')
    elif 60 < num <= 90:
        return parse(f'202004{convert_day_time(num-60)}')
    elif 90 < num <= 121:
        return parse(f'202005{convert_day_time(num-90)}')


def logistic_increase_function_nohubei_healadd(t, K, P0, r):
    t0 = 1
    # K = 13405
    exp_value = np.exp(r * (t - t0))
    value = (K * exp_value * P0) / (K + (exp_value - 1) * P0)
    return value


def nohubei_healadd_predict():
    result = {}
    ##读取训练好的模型
    popt = np.loadtxt(open(nohubei_cureIncr_model_path), delimiter=",", skiprows=0)
    ## 从2月20号公布的19号的确诊人数开始进行计算，即"i + 25"
    day_list = [i + 25 for i in range(100)]
    people_sick = logistic_increase_function_nohubei_healadd(np.array([day_list]), popt[4], popt[1], popt[3])
    for i in range(len(day_list)):
        if i == 0:
            continue
        '''
        day为21表示的是20号新增人数
        '''
        date_time = heal_convert_date(i + 20).date()
        if date_time >= today:
            result[date_time] = {
                'date': date_time,
                'forcastCureIncr': int(people_sick[0][i] - people_sick[0][i - 1])
            }
    return result


def logistic_increase_function_hubei_healadd(t, K, P0, r):
    t0 = 11
    exp_value = np.exp(r * (t - t0))
    value = (K * exp_value * P0) / (K + (exp_value - 1) * P0)
    return value


def hubei_healadd_predict():
    popt = np.loadtxt(open(hubei_cureIncr_model_path), delimiter=",", skiprows=0)
    people_sick = [int(logistic_increase_function_hubei_healadd(np.array([i + 26]), popt[4], popt[1], popt[3])) for i in range(100)]
    add_value = [people_sick[i + 1] - people_sick[i] for i in range(len(people_sick) - 1)]
    result = {}
    for i in range(len(add_value)):
        date_time = heal_convert_date(i + 21).date()
        if date_time >= today:
            result[date_time] = {
                'date': date_time,
                'forcastCureIncr': add_value[i]
            }
    return result


def logistic_increase_function_heal(t, K, P0, r):
    t0 = 1
    # K = 80000
    exp_value = np.exp(r * (t - t0))
    value = (K * exp_value * P0) / (K + (exp_value - 1) * P0)
    return value


def overall_healadd_predict():
    ##读取训练好的模型
    popt = np.loadtxt(open(heal_model_path), delimiter=",", skiprows=0)
    # 对未来50天进行预测
    day_list = [i + 27 for i in range(100)]
    people_sick = logistic_increase_function_heal(np.array([day_list]), popt[4], popt[1], popt[3])
    pre_day = {}

    for i in range(len(day_list)):
        if i == 0:
            continue
        '''
        day为19表示的是18号新增人数
        '''
        date_time = heal_convert_date(i + 18).date()
        if date_time >= today:
        # if 1:
            # real = ncov_dxy.find_one({'date': date_time.strftime('%m.%d')})
            # if real:
            #     real = real.get('overall', {}).get('curedIncr', 0)
            # else:
            #     real = 0
            pre_day[date_time] = {
                'date': date_time,
                # 'real': real,
                'forcast': int(people_sick[0][i] - people_sick[0][i - 1])
            }
            # pre_day.append({
            #     'date': date_time,
            #     'real': real,
            #     'forcast': int(people_sick[0][i] - people_sick[0][i - 1])
            # })
    return pre_day


def predict_all(pre_days):
    overall_confirm = overall_confirm_predict(pre_days)
    overall_healadd = overall_healadd_predict()
    for date, healadd in overall_healadd.items():
        if date in overall_confirm:
            # overall_confirm[date]['cureIncr'] = healadd['real']
            overall_confirm[date]['forcastCureIncr'] = healadd['forcast']
    return overall_confirm

def predict_nohubei(pre_days):
    nohubei_confirm = nohubei_confirm_predict(pre_days)
    nohubei_headadd = nohubei_healadd_predict()
    for date, headadd in nohubei_headadd.items():
        if date in nohubei_confirm:
            nohubei_confirm[date]['forcastCureIncr'] = headadd['forcastCureIncr']
    return nohubei_confirm

def logistic_increase_function_hubei_confirmIncr(t, K, P0, r):
    t0 = 11
    exp_value = np.exp(r * (t - t0))
    value = (K * exp_value * P0) / (K + (exp_value - 1) * P0)
    return value

def hubei_confirmIncr_predict():
    popt = np.loadtxt(open(hubei_confirmIncr_model_path), delimiter=",", skiprows=0)
    people_sick = [int(logistic_increase_function_hubei_confirmIncr(np.array([i + 29]), popt[4], popt[1], popt[3])) for i in range(100)]
    pre_day = {}
    for i in range(len(people_sick) - 1):
        date_time = heal_convert_date(i + 19).date()
        if date_time == yesterday:
            yes_confirm = yes_data.get('hubei_confirm', 0)
        if date_time >= today:
        # if 1:
            yes_date_time = heal_convert_date(i + 18).date()

            real = ncov_dxy.find_one({'date': date_time.strftime('%m.%d'), 'hubei_confirm': {'$exists': True}})
            yes_real = ncov_dxy.find_one({'date': yes_date_time.strftime('%m.%d')}) or {}
            if real:
                confirmedIncr = real.get('hubei_confirm', 0) - yes_real.get('hubei_confirm', 0)
                cureIncr = real.get('hubei_cureIncr', 0)
                confirmed = real.get('hubei_confirm', 0)
            else:
                confirmedIncr = 0
                cureIncr = 0
                confirmed = 0
            forcastConfirmedIncr = people_sick[i + 1] - people_sick[i]
            pre_day[date_time] = {
                'date': date_time,
                'confirmedIncr': confirmedIncr,
                'forcastConfirmedIncr': forcastConfirmedIncr,
                'cureIncr': cureIncr,
                'real': confirmed,
                'forcast': yes_confirm + forcastConfirmedIncr
            }
            yes_confirm += forcastConfirmedIncr

    return pre_day

def predict_hubei():
    confirmIncr = hubei_confirmIncr_predict()
    cureIncr = hubei_healadd_predict()
    for date, healadd in cureIncr.items():
        if date in confirmIncr:
            confirmIncr[date]['forcastCureIncr'] = healadd['forcastCureIncr']
    return confirmIncr

def get_predict_history():
    history = ncov_dxy.find_many({'date': {'$lt': today.strftime('%m.%d'), '$gt': '01.25'}, 'forcast_result': {'$exists': True}},
                                 {'forcast_result': 1, 'date': 1})
    overall = []
    hubei = []
    nohubei = []
    for h in history:
        fres = h['forcast_result']
        if 'overall' in fres:
            overall.append(fres['overall'])
        if 'hubei' in fres:
            hubei.append(fres['hubei'])
        if 'overall' in fres:
            nohubei.append(fres['nohubei'])
    return overall, hubei, nohubei


def predict_world():
    ret = {}
    data = world_col.find_many({}).sort([('date', 1)])
    for i in data:
        date = i['date']
        name = i['name']
        if name == 'nochina':
            total = nw_col.find_one({'date': date, 'country': 'Total'})
            china = nw_col.find_one({'date': date, 'country': 'China'})
            if total and china:
                confirmedCount = total['confirmedCount'] - china['confirmedCount']
            else:
                confirmedCount = 0
        else:
            if name == 'United States':
                name = 'United States of America'
            real = nw_col.find_one({'date': date, 'country': name})
            confirmedCount = real['confirmedCount'] if real else 0
        if name not in ret:
            ret[name] = [{'date': date, 'real': confirmedCount, 'forcast': i['forcast']}]
        else:
            ret[name].append({'date': date, 'real': confirmedCount, 'forcast': i['forcast']})
    return ret


def predict():
    overall = predict_all(100)
    nohubei = predict_nohubei(100)
    hubei = predict_hubei()
    for date, data in hubei.items():
        if date in overall and date in nohubei and 'forcastConfirmedIncr' in data and 'forcastConfirmedIncr' in nohubei[date]:
            overall[date]['forcastConfirmedIncr'] = data['forcastConfirmedIncr'] + nohubei[date]['forcastConfirmedIncr']
    yes_overall_confirm = yes_data.get('overall', {}).get('confirmedCount', 0)

    for date, overitem in overall.items():
        if 'forcastConfirmedIncr' in overitem:
            overitem['forcast'] = overitem['forcastConfirmedIncr'] + yes_overall_confirm
            yes_overall_confirm += overitem['forcastConfirmedIncr']
    overall_res, hubei_res, nohubei_res = get_predict_history()

    overall_res.extend(list(overall.values()))
    hubei_res.extend(list(hubei.values()))
    nohubei_res.extend(list(nohubei.values()))

    ret = {
        'overall': overall_res,
        'nohubei': nohubei_res,
        'hubei': hubei_res,
        'world': predict_world()
    }
    return ret


if __name__ == '__main__':
    ret = predict_nohubei(40)
    for i in ret.values():
        print(i)
    # ret = nohubei_confirm_predict(40)
    # for i in ret.values():
    #     print(i)
    # predict(40)
    # print(list(ret.values())[24])
    # ret = nohubei_confirm_predict()
    # print(ret)
    # ret = hubei_confirmIncr_predict()
    # print(ret)

    # itemdxy14 = ncov_dxy.find_one({'date': '02.13'})
    # # itemtx14 = ncov.find_one({'date': '02.14'})
    # hubei = itemdxy14['area'][0]['confirmedCount']
    # nohubei = sum([i['confirmedCount'] for i in itemdxy14['area'][1:]])
    # print(hubei, nohubei)



    # data = json.load(open('/Users/AMiner/Documents/result.json'))
    # dic = {}
    # for area, results in data.items():
    #     for r in results:
    #         r['area'] = area
    #         if r['date'] in dic:
    #             dic[r['date']].append(r)
    #         else:
    #             dic[r['date']] = [r]
    # # print(dic)
    # insert_data = {}
    # for date, ret in dic.items():
    #     date_str = '.'.join(date.split('-')[1:])
    #     items = {}
    #     for i in ret:
    #         area = i.pop('area')
    #         items[area] = i
    #     insert_data[date_str] = items
    #
    # for k, v in insert_data.items():
    #     ncov_dxy.update_one({'date': k}, {'$set': {'forcast_result': v}})



