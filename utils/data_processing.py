# -*- coding: utf-8 -*-
# @Time    : 2020/7/10 2:38 PM
# @Author  : Bing_Lun
# @Email   :  bing.lun@aminer.cn
# @File    : data_processing.py
# @Software : PyCharm

from apps.mongo_client import COVID_KG_ZH_EN, EVENT_ENTITY, Drop_ENTITIES, COVID_KG_HEAD_TAIL, COVID_PAPERS_REFERENCE, \
    COVID_KG_WORD_EVENTS, COVID_KG_ZH, COVID_QA_relation
from apps.ncov.sftp import baidu_translate
from bson import ObjectId
import datetime, csv, os

zh_en, event_entity = COVID_KG_ZH_EN(), EVENT_ENTITY()
drop_entity = Drop_ENTITIES()
head_tail = COVID_KG_HEAD_TAIL()
paper = COVID_PAPERS_REFERENCE()
word_event = COVID_KG_WORD_EVENTS()
covid_zh = COVID_KG_ZH()
qa_mongo = COVID_QA_relation()


def obtain_entities(entities, lang):
    result = []
    for line in entities:
        zh_en_result = zh_en.find_one({'url': line})
        result.append({'url': zh_en_result.get('url'), 'entity_name': zh_en_result.get('label_' + lang)})
    return result


def write_mongo_event_entity(url, event_id):
    entities = []
    event_entity_result = event_entity.find_one({'event_id': event_id})
    if event_entity_result:
        entities_url = event_entity_result.get('entities')
        if url not in entities_url:
            entities_url.append(url)
        event_entity.update_one({'_id': event_entity_result.get('_id')}, {'$set': {'entities': entities_url}})
    else:
        entities.append(url)
        event_entity.insert_one({'event_id': event_id, 'entities': entities})


def insert(entities, url, label_zh, label_en, relation_zh, suspected_relation):
    relation_en = baidu_translate(relation_zh, 'zh', 'en')
    su_relation = drop_entity.find_one({'url': suspected_relation})
    relation = head_tail.find_one({'head_zh': su_relation.get('label_zh'), 'tail_zh': label_zh})
    if relation_zh != '' and relation_en != '' and relation == None:
        head_tail.insert_one(
            {'head_url': suspected_relation.replace('Drop_', ''), 'head_zh': su_relation.get('label_zh'),
             'head_en': su_relation.get('label_en'),
             'relation_zh': relation_zh, 'relation_en': relation_en, 'tail_url': url, 'tail_zh': label_zh,
             'tail_en': label_en})


def inquire_event(entity_and_entity):
    title, source = '', ''
    entity_id = entity_and_entity.get('entities')
    event_id = entity_and_entity.get('event_id')
    new_entity = []
    for entity in entity_id:
        zh_en_result = zh_en.find_one({'url': entity})
        if zh_en_result == None:
            continue
        new_entity.append(
            {'url': entity, 'label_zh': zh_en_result.get('label_zh'), 'label_en': zh_en_result.get('label_en')})
    event_result_paper = paper.find_one({'_id': ObjectId(event_id)})
    event_result_event = word_event.find_one({'_id': ObjectId(event_id)})
    if event_result_paper:
        title = event_result_paper.get('title')
        source = 'paper'
    elif event_result_event:
        title = event_result_event.get('title')
        source = 'event'
    result = {'title': title, 'entities': new_entity, 'ObjectId': event_id, 'source': source}
    return result


def judge_abstractInfo(mogo_result, info):
    if mogo_result.get(info) == None:
        result = ''
    else:
        result = mogo_result.get(info)
    return result

def add_knowledge(knowledge, mongodb, url, label):
    if knowledge == None:
        if mongodb.find_one({'url': url, 'label': label, 'abstractInfo': None,
             'relations': [], 'img': None}) == None:
            mongodb.insert_one(
                {'url': url, 'label': label, 'abstractInfo': {'zhwiki':None, 'baidu':None, 'enwiki':None, 'COVID':{}},
                 'relations': [], 'img': None, 'createdate': datetime.datetime.now(),
                 'updatedate': datetime.datetime.now()})
    else:
        if mongodb.find_one({'url': url, 'label': knowledge.get('label'), 'abstractInfo': knowledge.get('abstractInfo'),
             'relations': knowledge.get('relations'), 'img': knowledge.get('img')}) == None:
            mongodb.insert_one(
                {'url': url, 'label': knowledge.get('label'), 'abstractInfo': knowledge.get('abstractInfo'),
                 'relations': knowledge.get('relations'), 'img': knowledge.get('img'), 'createdate': knowledge.get('createdata'),
                 'updatedate': datetime.datetime.now()})

def update_dict(entities_path, entities_zh_en):
    zh_en_result = zh_en.find_many({})
    f1 = open(entities_path, 'w')
    f2 = open(entities_zh_en, 'w')
    for line in zh_en_result:
        zh, en = line.get('label_zh'), line.get('label_en')
        f1.write(zh + '\n')
        f2.write(zh + '\n' + en + '\n')
    f1.close(), f2.close()

def update_QA_mongo():
    relation_result, zh_kg = head_tail.find_many({}), covid_zh.find_many({})
    for line in relation_result:
        triple = {'head_url':line.get('head_url'), 'head_name':line.get('head_zh'),
                    'relation':line.get('relation_zh'), 'tail_url':line.get('tail_url'),
                    'tail_name':line.get('tail_zh')}
        qa_mongo_result = qa_mongo.find_one(triple)
        if qa_mongo_result:
            continue
        qa_mongo.insert_one(triple)
    for line in zh_kg:
        head_url, head_name = line.get('url'), line.get('label')
        if line.get('abstractInfo') == None or line.get('abstractInfo').get('COVID') == None:
            continue
        for i in line.get('abstractInfo').get('COVID'):
            tail = line.get('abstractInfo').get('COVID').get(i)
            triple = {'head_url':head_url, 'head_name':head_name,
                        'relation':i, 'tail_url':None,
                        'tail_name':tail}
            qa_mongo_result = qa_mongo.find_one(triple)
            if qa_mongo_result:
                continue
            qa_mongo.insert_one(triple)
