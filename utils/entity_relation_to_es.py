#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: xuwei
Email: 18810079020@163.com
File: data_to_es.py
Date: 2020/7/8 1:32 下午
'''

import pandas as pd
from general_tools.elasticsearch_op import get_es_client,EsOperate
from elasticsearch_dsl import Document, Text, Keyword

'''
general_tools==0.4.7
elasticsearch-dsl==7.2.0
'''

class Faq(Document):
    question = Text(analyzer='ik_max_word')
    answer = Text(analyzer='ik_max_word')

    class Index:
        name = 'faq'
        using = 'es'


class Entity(Document):
    name_k = Keyword()
    name = Text(analyzer='ik_max_word')

    class Index:
        name = 'entity'
        using = 'es'


class Relation(Document):
    name_k = Keyword()
    name = Text(analyzer='ik_max_word')

    class Index:
        name = 'relation'
        using = 'es'



class EntityToEs(object):
    def __init__(self):
        self.es_con = get_es_client(host='http://192.168.6.221:9200', user='admin', password='admin@2020')
        self.es_op = EsOperate(self.es_con, Entity.Index.name)

    def etl_data_to_es(self, file):
        df = pd.read_csv(file)
        df.dropna(inplace=True)
        df['_id'] = df['name']
        df['name_k'] = df['name']
        write_list = df.to_dict('records')
        self.es_op.bulk_to_es(write_list)


class RelationToEs(object):
    def __init__(self):
        es_con = get_es_client(host='http://192.168.6.221:9200', user='admin', password='admin@2020')
        self.es_op = EsOperate(es_con, Relation.Index.name)

    def etl_data_to_es(self, file):
        df = pd.read_csv(file)
        df.dropna(inplace=True)
        df['_id'] = df['name']
        df['name_k'] = df['name']
        write_list = df.to_dict('records')
        self.es_op.bulk_to_es(write_list)


if __name__ == '__main__':
    toEs = EntityToEs()
    # toEs.etl_data_to_es(file_path + '/data/entity_name.csv')

    # toEs = RelationToEs()
    # toEs.etl_data_to_es(file_path + '/data/relation_name.csv')