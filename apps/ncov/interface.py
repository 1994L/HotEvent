import datetime, difflib, math, os, re, xlrd, xlwt, jieba, csv
from apps.mongo_client import COVID_KG_EN, COVID_KG_ZH, COVID_KG_HEAD_TAIL, ENTITY_HOT, COVID_QA_relation, deficiency_QA
from apps.mongo_client import Drop_ENTITIES, Drop_RELATIONS, Drop_ZH_KNOWLEDGE, Drop_EN_KNOWLEDGE, EVENT_ENTITY
from apps.mongo_client import NcovWHOWorldDB, NcovInflowsDB, NcovChangeLogDB, COVID_KG_ZH_EN, COVID_KG_WORD_EVENTS
from apps.ncov.ncov_crawler import Crawler
from apps.ncov.sftp import uploadFile, downloadFile, baidu_translate
from utils.data_processing import write_mongo_event_entity, insert, inquire_event, judge_abstractInfo, add_knowledge, update_QA_mongo
from utils.entity_relation_to_es import EntityToEs, RelationToEs
from utils.decorators import timing
from utils.string_helper import contain_zh, remove_symbol_nospace, get_split_py, pinyin2hanzi
import requests

qa_relation = COVID_QA_relation()
nw_col = NcovWHOWorldDB()
nf_col = NcovInflowsDB()
cl_col = NcovChangeLogDB()
en_zh_covid = COVID_KG_ZH_EN()
zh_covid_mo = COVID_KG_ZH()
en_covid_mo = COVID_KG_EN()
head_tail = COVID_KG_HEAD_TAIL()
entity_hot, d_QA = ENTITY_HOT(), deficiency_QA()
event_entity, word_event = EVENT_ENTITY(), COVID_KG_WORD_EVENTS()
drop_entity, drop_relation, drop_zhknowledge, drop_enknowledge = Drop_ENTITIES(), Drop_RELATIONS(), Drop_ZH_KNOWLEDGE(), Drop_EN_KNOWLEDGE()
model_path = os.path.join(os.path.dirname(__file__), 'model')

zh_en_covid = {'新冠肺炎', '新型冠状病毒肺炎', 'covid-19', '2019-ncov', 'novel coronavirus pneumonia', 'ncp'}
zh_en_sars = {'新冠病毒', '新型冠状病毒', '新冠', 'sars-cov-2', 'novel coronavirus'}
file_path_ = os.path.join(os.path.dirname(__file__), 'model')

# query_weight = 100


@timing
def ncov_world_v1():
    country = ['中国', '韩国', '加拿大', '日本', '新加坡', '德国', '法国', '其他']
    data = nw_col.find_many({}).sort([('date', 1)])
    ret = []
    country_dict = {i: [] for i in country}
    country_zh2en = {}
    for i in data:
        i.pop('_id')
        country = i.pop('country')
        country_zh = i.pop('country_zh')
        if country_zh in country_dict:
            country_zh2en[country_zh] = country
            country_dict[country_zh].append(i)
        else:
            country_zh2en['其他'] = 'other'
            country_dict['其他'].append(i)
    others_dict = {}
    for i in country_dict['其他']:
        if i['date'] in others_dict:
            others_dict[i['date']].append(i)
        else:
            others_dict[i['date']] = [i]
    others = []
    for k, v in others_dict.items():
        initial = v[0]
        for vv in v[1:]:
            for key in initial:
                if key != 'date':
                    initial[key] = initial[key] + vv[key]
        others.append(initial)
    country_dict['其他'] = others
    for name_zh, datas in country_dict.items():
        if name_zh in country_zh2en:
            ret.append({
                'name_zh': name_zh,
                'name': country_zh2en[name_zh],
                'data': datas
            })

    return ret


@timing
def ncov_world():
    data = nw_col.find_many({}).sort([('date', 1)])
    ret = []
    country_zh2en = {}
    country_dict = {}
    for i in data:
        i.pop('_id')
        country = i.pop('country')
        country_zh = i.pop('country_zh')
        country_dict.setdefault(country_zh, [])
        country_dict[country_zh].append(i)
        country_zh2en.setdefault(country_zh, country)
    for name_zh, datas in country_dict.items():
        if name_zh in country_zh2en:
            ret.append({
                'name_zh': name_zh,
                'name': country_zh2en[name_zh],
                'data': datas
            })

    return ret


def ncov_inflows():
    '''
    流入病例
    :return:
    '''
    data = nf_col.find_many({})
    ret = []
    for i in data:
        item = {}
        source = {
            'country': i.get('from_country', ''),
            'province': '',
            'city': i.get('from_city', ''),
            'pos': i.get('from_lng_lat', [])
        }
        target = {
            'country': '中国',
            'province': i.get('to_country', ''),
            'city': i.get('to_city', ''),
            'pos': i.get('to_lng_lat', [])
        }
        if i.get('traffic_info'):
            source['time'] = i['traffic_info'][0].get('traffic_time', '')
            target['time'] = i['traffic_info'][-1].get('traffic_time', '')
        item['source'] = source
        item['target'] = target
        item['confirmedTime'] = i.get('confirmed_date', '')
        if i.get('gender') == '男':
            item['gender'] = 1
        elif i.get('gender') == '女':
            item['gender'] = 0
        ret.append(item)
    return ret


def ncov_china():
    crawler = Crawler()
    overall, area = crawler.crawler()
    world_data = nw_col.find_many({'country': 'Total'}).sort([('date', -1)])
    overall['worldConfirmedCount'] = world_data[0].get('confirmedCount')
    overall['worldDeadCount'] = world_data[0].get('deadCount')
    overall['worldConfirmedAddCount'] = world_data[0].get('confirmedAddCount')
    overall['worldDeadAddCount'] = world_data[0].get('deadAddCount')
    ret = {
        'overall': overall,
        'area': area
    }
    return ret


def predict_changelog():
    ret = cl_col.cursor2list(cl_col.query_sort({}, [('time', -1)]), convert={'id': '_id.str'})
    return ret


def gain_pos(newstext, entity):
    pos_result = []
    for i in range(len(newstext)):
        if newstext[i:i + len(entity)] == entity:
            pos_result.append({'start': i, 'end': i + len(entity)})
    return pos_result


def obtain_weight(i):
    if i <= 50:
        query = i * 20
    elif i > 50 and i < 80:
        query = (i - 50) * 15 + 1000
    else:
        query = (i - 80) * 10 + 1450
    return query


def get_answer(newstext):
    entity_data = list(open(f"{model_path}/entities_zh_en.txt", encoding='utf-8'))
    answer = []
    hot_max = entity_hot.find_one({'max_min': 1}).get('value')
    if contain_zh(newstext) == False:
        news = ' ' + re.sub("[\s+\.\!\/_,$%^*(\"\']+|[+！，。？、~@#￥%……&*（）]+", " ", newstext.lower()) + ' '
        for i in set(entity_data):
            i = ' ' + i.strip('\n') + ' '
            query_result = {}
            if i not in news:
                continue
            i = i.strip()
            if i in zh_en_covid:
                i = 'covid-19'
            if i in zh_en_sars:
                i = 'sars-cov-2'
            query_entity_result = en_zh_covid.find_one({'label_en': i})
            if query_entity_result is None:
                continue
            entity_event = query_entity_result.get('hot_event') + 1
            hot_query = obtain_weight(query_entity_result.get('hot_query'))
            hot_ = entity_event + hot_query
            en_zh_covid.update_one({'_id': query_entity_result.get('_id')},
                                   {'$set': {'hot_event': entity_event, 'hot': hot_}})
            sound_regex = re.compile(i, re.I)
            input_entity = sound_regex.search(newstext)
            obtain_request(query_entity_result.get('url'), input_entity[0], 'en', query_result)
            hot = math.log(max(hot_ - 0, 1)) / math.log(hot_max - 0)
            pos = gain_pos(newstext, input_entity[0])
            query_result['pos'], query_result['hot'] = pos, hot
            answer.append(query_result)
    else:
        jieba.load_userdict(f'{model_path}/entities.txt')
        word_list = jieba.cut(newstext, cut_all=False)
        for i in set(word_list):
            original_entity, query_result = i, {}
            if i in zh_en_covid:
                i = '新型冠状病毒肺炎'
            if i in zh_en_sars:
                i = '新型冠状病毒'
            if i + '\n' not in set(entity_data):
                continue
            query_entity_result = en_zh_covid.find_one({'label_zh': i})
            if query_entity_result is None:
                continue
            entity_event = query_entity_result.get('hot_event') + 1
            hot_query = obtain_weight(query_entity_result.get('hot_query'))
            hot_ = entity_event + hot_query
            en_zh_covid.update_one({'_id': query_entity_result.get('_id')},
                                   {'$set': {'hot_event': entity_event, 'hot': hot_}})
            obtain_request(query_entity_result.get('url'), original_entity, 'zh', query_result)
            hot = math.log(max(hot_ - 0, 1)) / math.log(hot_max - 0)
            pos = gain_pos(newstext, original_entity)
            query_result['pos'], query_result['hot'] = pos, hot
            answer.append(query_result)
    return answer


def get_equal_rate(str1, str2):
    '''
    判断字符串相似度
    :param str1:
    :param str2:
    :return:
    '''
    return difflib.SequenceMatcher(None, str1, str2).quick_ratio()


def get_entity_relation(input_url, lang):
    relations, query_lang, result = [], '', {}
    hot_max = entity_hot.find_one({'max_min': 1}).get('value')
    entity = en_zh_covid.find_one({'url': input_url})
    if lang == 'en':
        mongo_result, query_lang = en_covid_mo.find_one({'url': input_url}), 'en'
    else:
        mongo_result, query_lang = zh_covid_mo.find_one({'url': input_url}), 'zh'
    result['label'], result['url'], result['abstractInfo'] = mongo_result.get('label'), mongo_result.get('url'), {}
    result['abstractInfo']['enwiki'], result['abstractInfo']['baidu'] = judge_abstractInfo(
        mongo_result.get('abstractInfo'), 'enwiki'), judge_abstractInfo(mongo_result.get('abstractInfo'), 'baidu')
    result['abstractInfo']['zhwiki'], result['abstractInfo']['COVID'] = judge_abstractInfo(mongo_result.get('abstractInfo'), 'zhwiki'), {}
    if mongo_result.get('abstractInfo').get('COVID') != None:
        result['abstractInfo']['COVID']['properties'] = mongo_result.get('abstractInfo').get('COVID')
    else:
        result['abstractInfo']['COVID']['properties'] = dict()
    gain_reverse_relation(mongo_result.get('url'), relations, query_lang, mongo_result.get('label_' + lang))
    result['abstractInfo']['COVID']['relations'] = relations
    result['img'] = mongo_result.get('img')
    hot_entity = obtain_weight(entity.get('hot_query')) + entity.get('hot_event')
    hot = (math.log(max(hot_entity - 0, 1))) / math.log(hot_max - 0)
    result['hot'] = min(1, hot)
    return result


def gain_reverse_relation(url, relations, lang, input_entity):
    for line in head_tail.find_or([{'head_url': url}, {'tail_url': url}]):
        if line.get('tail_' + lang) == input_entity:
            relations.append(
                {'relation': line.get('relation_' + lang).replace('_', ' '),
                 'url': line.get('head_url'),
                 'label': line.get('head_' + lang), 'forward': False})
        else:
            relations.append(
                {'relation': line.get('relation_' + lang).replace('_', ' '),
                 'url': line.get('tail_url'),
                 'label': line.get('tail_' + lang), 'forward': True})


def obtain_request(queryentity, input_entity, lang, result):
    relations, query_lang = [], ''
    if lang == 'en':
        mongo_result, query_lang = en_covid_mo.find_one({'url': queryentity}), 'en'
    else:
        mongo_result, query_lang = zh_covid_mo.find_one({'url': queryentity}), 'zh'
    result['label'], result['url'], result['abstractInfo'] = input_entity, mongo_result.get('url'), {}
    result['abstractInfo']['enwiki'], result['abstractInfo']['baidu'] = judge_abstractInfo(mongo_result.get('abstractInfo'), 'enwiki'), \
                                                                        judge_abstractInfo(mongo_result.get('abstractInfo'), 'baidu')
    result['abstractInfo']['zhwiki'], result['abstractInfo']['COVID'] = judge_abstractInfo(mongo_result.get('abstractInfo'), 'zhwiki'),\
                                                                        {}
    if mongo_result.get('abstractInfo').get('COVID') != None:
        result['abstractInfo']['COVID']['properties'] = mongo_result.get('abstractInfo').get('COVID')
    else:
        result['abstractInfo']['COVID']['properties'] = dict()
    gain_reverse_relation(mongo_result.get('url'), relations, query_lang, input_entity)
    result['abstractInfo']['COVID']['relations'] = relations
    result['img'] = mongo_result.get('img')


def sort(entity_list):
    final_result = []
    entity_list.sort(key=lambda x: x["score"], reverse=True)
    if len(entity_list) < 1:
        return final_result
    if entity_list[0].get('score') == 1.0:
        final_result.append(entity_list[0]), entity_list.pop(0)
        entity_list.sort(key=lambda y: y["hot"], reverse=True)
        final_result.extend(entity_list)
    else:
        entity_list.sort(key=lambda y: y["hot"], reverse=True)
        final_result.extend(entity_list)
    return final_result


def obtain_query_result(entity, zh_en_covid, zh_en_sars, lang, answer, mini):
    hot_max, result = entity_hot.find_one({'max_min': 1}).get('value'), []
    if lang == 'en':
        if entity in zh_en_covid:
            entity = 'covid-19'
        if entity in zh_en_sars:
            entity = 'sars-cov-2'
    else:
        if entity in zh_en_covid:
            entity = '新型冠状病毒肺炎'
        if entity in zh_en_sars:
            entity = '新型冠状病毒'
    if mini == 1:
        entity_result = en_zh_covid.find_one({'label_' + lang: entity})
        answer.append({'label_zh': entity_result.get('label_zh'), 'label_en': entity_result.get('label_en')})
    elif mini == 0:
        if len(entity) < 3:
            entityLen = len(entity) * 3
            query_entity_result = en_zh_covid.find_many({'label_' + lang: {'$regex': entity}, 'table': True,
                                                         '$where': "(this.label_" + lang + ".length <=" + str(
                                                             entityLen) + ")"})
        else:
            query_entity_result = en_zh_covid.find_many({'label_' + lang: {'$regex': entity}, 'table': True})
        for line in query_entity_result:
            del line['_id']
            score = get_equal_rate(entity, line.get('label_' + lang))
            hot = min(1.0, (math.log(max(line.get('hot') - 0, 1))) / math.log(hot_max - 0))
            line['score'], line['hot'] = score, hot
            result.append(line)
        final_result = sort(result)
        result.clear(), result.extend(final_result)
        if len(final_result) >= 15:
            final_result = final_result[0:15]
        for line in final_result:
            query_i_result = {'hot': line.get('hot')}
            obtain_request(line.get('url'), line.get('label_' + lang), lang, query_i_result)
            answer.append(query_i_result)


def query_entity(input_entity, mini):
    entity, query_result, answer = input_entity.strip('.').strip().lower(), {}, []
    if entity:
        if contain_zh(entity) == False:
            obtain_query_result(entity, zh_en_covid, zh_en_sars, 'en', answer, mini)
        else:
            obtain_query_result(entity, zh_en_covid, zh_en_sars, 'zh', answer, mini)
    return answer


def update_hot(url):
    result, hot_max, answer = en_zh_covid.find_one({'url': url}), entity_hot.find_one({'max_min': 1}).get('value'), []
    query_value = result.get('hot_query') + 1
    query_hot = obtain_weight(query_value)
    hot_entity = query_hot + result.get('hot_event')
    en_zh_covid.update_one({'_id': result.get('_id')}, {'$set': {'hot_query': query_value, 'hot': hot_entity}})
    return answer


def lenovo_result(entity_name, lang, result):
    hot_max = entity_hot.find_one({'max_min': 1}).get('value')
    if lang == 'zh':
        result_mongo = en_zh_covid.find_many({'label_' + lang: {'$regex': '^' + entity_name}, 'table': True}).sort(
            "hot", -1).limit(10)
    else:
        result_mongo = en_zh_covid.find_many(
            {'label_' + lang: {'$regex': '^' + entity_name, '$options': '$i'}, 'table': True}).sort(
            "hot", -1).limit(5)
    for line in result_mongo:
        hot = min(1.0, (math.log(max(line.get('hot') - 0, 1))) / math.log(hot_max - 0))
        result.append(
            {'url': line.get('url'), 'label_zh': line.get('label_zh'), 'label_en': line.get('label_en'), 'lang': lang,
             'hot': hot})


def lenovo_entity(entity):
    entity, answer = remove_symbol_nospace(entity).lower(), []
    if entity == False:
        return answer
    if contain_zh(entity):
        lenovo_result(entity, 'zh', answer)
    else:
        if len(entity) < 2:
            return answer
        pinyin_list, _, _ = get_split_py(entity)
        text_list = pinyin2hanzi(pinyin_list)
        for line in text_list:
            lenovo_result(line[0], 'zh', answer)
        lenovo_result(entity, 'en', answer)
        answer.sort(key=lambda x: x['hot'], reverse=True)
        answer = answer[0:9]
    return answer


def downloads(file_path, nums):
    answer = []
    result = drop_entity.find_many({'update_time': nums})
    try:
        workbook = xlwt.Workbook(encoding='GBK')
        worksheet = workbook.add_sheet('sheet 1', cell_overwrite_ok=True)
        title = ['suspected_relation', 'url', 'label_zh', 'label_en', 'table', 'belongTo', 'relation', 'event_id',
                 'create_date']
        for i in range(len(title)):
            worksheet.write(0, i, title[i])
        i = 0
        for line in result:
            url, label_zh, label_en, table, event_id, create_date = line.get('url'), line.get('label_zh'), line.get(
                'label_en'), 'False', line.get('event_id'), line.get('create_date')
            relation_result = drop_relation.find_one({'head_url': url, 'relation_zh': '属于'})
            if relation_result == None:
                continue
            i += 1
            worksheet.write(i, 0, ''), worksheet.write(i, 1, url), worksheet.write(i, 2, label_zh), worksheet.write(i, 3 ,label_en), \
            worksheet.write(i, 4, table), worksheet.write(i, 5, relation_result.get('tail_zh')), worksheet.write(i, 6, ''), worksheet.write(
                i, 7, event_id), worksheet.write(i, 8, create_date)
            for su_line in line.get('suspected_relation'):
                i += 1
                su_url, su_label_zh, su_label_en = su_line.get('url'), su_line.get('label_zh'), su_line.get('label_en')
                worksheet.write(i, 0, url), worksheet.write(i, 1, su_url), worksheet.write(i, 2,
                                                                                           su_label_zh), worksheet.write(
                    i, 3, su_label_en)
        workbook.save(file_path)
        uploadFile(file_path, '/misc/Drop_Covid/entities_labeled.xls')
        os.remove(file_path)
        answer.append('下载成功！！！！')
    except:
        answer.append('下载失败！！！')
    return answer


def update_dropmongo(url, entity_zh, entity_en, mongodb):
    result = mongodb.find_one({'url': url})
    if 'update_time' in result:
        update_time = result.get('update_time') + 1
    else:
        update_time = 0
    mongodb.update_one({'_id': result.get('_id')}, {'$set': {'update_time': update_time}})


def write_entity_and_relation(url, entity_zh, entity_en, belongTo, event_id):
    drop_entity_result = drop_entity.find_one({'url': url})
    event_id = drop_entity_result.get('event_id')
    url_ = url.replace('Drop_', '').replace(' ', '_')
    '''
    添加实体
    '''
    if en_zh_covid.find_one({'label_zh': entity_zh}) == None:
        en_zh_covid.insert_one(
            {'url': url_, 'label_zh': entity_zh, 'label_en': entity_en, 'table': True, 'hot_event': 0, 'hot_query': 0,
             'hot': 0, 'event_id': event_id})
    '''
    添加关系
    '''
    result_ = drop_relation.find_one({'head_url': url, 'relation_zh': '属于'})
    class_result = en_zh_covid.find_one({'label_zh': belongTo})
    if class_result == None:
        entity_translate_en = baidu_translate(belongTo, 'zh', 'en')
        new_url = 'https://covid-19.aminer.cn/kg/class/' + entity_translate_en
    else:
        new_url = class_result.get('url')
        entity_translate_en = class_result.get('label_en')
    drop_relation.update_one({'_id':result_.get('_id')}, {'$set':{'tail_url':new_url, 'tail_zh':belongTo, 'tail_en':entity_translate_en}})
    relation = drop_relation.find_one({'head_url': url})
    zh_knowledge, en_knowledge = drop_zhknowledge.find_one({'url': url}), drop_enknowledge.find_one({'url': url})
    tail_url = relation.get('tail_url').replace('Drop_', '').replace(' ', '_')
    relation_result = head_tail.find_one(
        {'head_url': url_, 'head_zh': entity_zh, 'head_en': entity_en, 'relation_zh': relation.get('relation_zh'),
         'tail_url': tail_url, 'tail_zh': relation.get('tail_zh'), 'tail_en': relation.get('tail_en')})
    if relation_result == None:
        head_tail.insert_one(
            {'head_url': url_, 'head_zh': entity_zh, 'head_en': entity_en, 'relation_zh': relation.get('relation_zh'),
             'relation_en': relation.get('relation_en'), 'tail_url': tail_url, 'tail_zh': relation.get('tail_zh'),
             'tail_en': relation.get('tail_en')})
    '''
    添加知识
    '''
    add_knowledge(zh_knowledge, zh_covid_mo, url_, entity_zh)
    add_knowledge(en_knowledge, en_covid_mo, url_, entity_en)
    write_mongo_event_entity(url_, event_id)




def update_mongo(data_path, file_path):
    answer = []
    try:
        downloadFile('/misc/Drop_Covid/entities_labeled.xls', data_path)
        workbook = xlrd.open_workbook(data_path)
        tabble = workbook.sheet_by_name('sheet 1')
        rows = tabble.nrows
        entities = {}
        for row in range(rows):
            row_data = tabble.row_values(row)
            if row_data[0] == 'suspected_relation':
                continue
            suspected_relation, url, label_zh, label_en, table, belongTo,relation_zh, event_id = row_data[0], row_data[1], row_data[2], \
                                                                              row_data[3], str(row_data[4]), row_data[5], row_data[6], row_data[7]
            if table.lower() == 'true':
                write_entity_and_relation(url, label_zh, label_en, belongTo, event_id)
                entities[url] = {'label_zh': label_zh, 'label_en': label_en, 'table':table}
                update_dropmongo(url, label_zh, label_en, drop_entity)
            elif table == '' and relation_zh != '':
                if suspected_relation in entities:
                    insert(entities, url, label_zh, label_en, relation_zh, suspected_relation)
            elif table.lower() == 'false':
                update_dropmongo(url, label_zh, label_en, drop_entity)
        obtain_entity_relation(file_path)
        update_QA_mongo()
        answer.append('更新成功！！！！')
    except:
        answer.append('更新失败！！！！！')
    return answer


def QA_answers(entity, relation):
    answer = []
    try:
        if entity in zh_en_covid:
            entity = '新型冠状病毒肺炎'
        if entity in zh_en_sars:
            entity = '新型冠状病毒'
        mongo_result = qa_relation.find_many({'head_name': entity, 'relation': relation})
        for line in mongo_result:
            if line.get('tail_name') == None:
                continue
            tail_url = line.get('tail_url', '')
            answer.append({'entity_name': line.get('tail_name'), 'entity_url': tail_url})
        return answer
    except:
        return answer

def obtain_entity_relation(file_path):
    entity_result, relation_result, zh_kg_result = en_zh_covid.find_many({}), head_tail.find_many({}), zh_covid_mo.find_many({})
    entity_f, relation_f = open(f'{file_path}/entity_name.csv', 'w+'), open(f'{file_path}/relation_name.csv', 'w+')
    entity, relation = csv.writer(entity_f), csv.writer(relation_f)
    entity.writerow(['name']), relation.writerow(['name'])
    relation_set = set()
    for line in entity_result:
        entity.writerow([line.get('label_zh')])
    for line in relation_result:
        relation_set.add(line.get('relation_zh'))
    for line in zh_kg_result:
        if line.get('abstractInfo') == None or line.get('abstractInfo').get('COVID') == None:
            continue
        for line in line.get('abstractInfo').get('COVID'):
            relation_set.add(line)
    for line in relation_set:
        relation.writerow([line])
    entity_f.close(), relation_f.close()
    EtoEs, RtoEs = EntityToEs(), RelationToEs()
    EtoEs.etl_data_to_es(f'{file_path}/entity_name.csv'), RtoEs.etl_data_to_es(f'{file_path}/relation_name.csv')


def show_update():
    answer = []
    event_entity_result = event_entity.find_many({})
    i = 0
    for line in event_entity_result:
        if i > 100:
            break
        event_entity_result = inquire_event(line)
        if event_entity_result.get('entities') == []:
            continue
        answer.append(event_entity_result)
    return answer

def analysis_result(answers, question):
    result = []
    if answers == []:
        d_QA.insert_one({'question': question})
    for answer in answers:
        answer_link = get_answer(answer.get('answer'))
        result.append({'answer':answer.get('answer'), 'entities':answer_link, 'match_question':answer.get('match_question'),
                       'score':answer.get('score'), 'source':answer.get('source')})
    return result


def QA(question):
    results = []
    result = requests.get("http://192.168.6.221:2000/aminer/get_answer?question=%s" % (question)).json()
    answers = analysis_result(result.get('data').get('answers'), question)
    results.append({'answers': answers, 'question': question})
    return results


if __name__ == '__main__':
    QA_answers('尼沃卢单抗', '属于')