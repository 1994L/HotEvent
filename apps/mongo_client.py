import os

from pymongo import MongoClient
from config import config
from pymongo.errors import AutoReconnect


MONGO_CONFIG = config.get(os.getenv('FLASK_CONFIG', 'development')).MONGO_CONFIG

__all__ = [
    'nCovCasesDB',
    'nCovCasesDXYDB',
    'NcovChangeLogDB',
    'NcovWHOWorldDB',
    'NcovInflowsDB',
    'NcovWorldPredictDB',
    'CovidDatasetDB',
    'FeedbackDB',
    'COVID_KG_ZH_EN',
    'COVID_KG_EN',
    'COVID_KG_ZH',
    'COVID_KG_HEAD_TAIL',
    'ENTITY_HOT',
    'Drop_ENTITIES',
    'Drop_RELATIONS',
    'Drop_ZH_KNOWLEDGE',
    'Drop_EN_KNOWLEDGE',
    'COVID_QA_relation',
    'deficiency_QA',
    'COVID_PAPERS_REFERENCE'
]

def retry_if_auto_reconnect_error(exception):
    return isinstance(exception, AutoReconnect)


class MG(object):
    def __init__(self, config):
        self.client = MongoClient(
            host=config['host'],
            port=config['port'],
            username=config['user'],
            password=config['password'],
            authSource=config['authdb'],
            connect=False
        )
        self.db = self.client[config['db_name']]

"""
mongodb_operation 静态方法 用来和mongodb 操作交互 
"""
class BaseHandle(object):
    @staticmethod
    def insert_one(collection, data):
        """直接使用insert() 可以插入一条和插入多条 不推荐 明确区分比较好"""
        res = collection.insert_one(data)
        return res.inserted_id

    @staticmethod
    def insert_many(collection, data_list):
        res = collection.insert_many(data_list)
        return res.inserted_ids

    @staticmethod
    def find_one(collection, data, data_field={}):
        if len(data_field):
            res = collection.find_one(data, data_field)
        else:
            res = collection.find_one(data)
        return res

    @staticmethod
    def find_many(collection, data, data_field={}):
        """ data_field 是指输出 操作者需要的字段"""
        if len(data_field):
            res = collection.find(data, data_field)
        else:
            res = collection.find(data)
        return res

    @staticmethod
    def update_one(collection, data_condition, data_set):
        """修改一条数据"""
        res = collection.update_one(data_condition, data_set)
        return res

    @staticmethod
    def update_many(collection, data_condition, data_set):
        """ 修改多条数据 """
        res = collection.update_many(data_condition, data_set)
        return res

    @staticmethod
    def replace_one(collection, data_condition, data_set):
        """ 完全替换掉 这一条数据， 只是 _id 不变"""
        res = collection.replace_one(data_condition, data_set)
        return res

    @staticmethod
    def delete_many(collection, data):
        res = collection.delete_many(data)
        return res

    @staticmethod
    def delete_one(collection, data):
        res = collection.delete_one(data)
        return res


'''
mongodb_base 和mongo 连接的信息 
'''
class DBBase(object):
    """ 各种query 中的数据 data 和 mongodb 文档中的一样"""

    def __init__(self, collection, mongo_config=MONGO_CONFIG):
        self.client = MG(mongo_config)
        self.collection = self.client.db[collection]

    def insert_one(self, data):
        res = BaseHandle.insert_one(self.collection, data)
        return res

    def insert_many(self, data_list):
        res = BaseHandle.insert_many(self.collection, data_list)
        return res

    def update_one(self, data_condition, data_set):
        res = BaseHandle.update_one(self.collection, data_condition, data_set)
        return res

    def update_many(self, data_condition, data_set):
        res = BaseHandle.update_many(self.collection, data_condition, data_set)
        return res

    #  ========================= Query Documents Start =========
    def find_one(self, data, data_field={}):
        res = BaseHandle.find_one(self.collection, data, data_field)
        return res

    def find_many(self, data, data_field={}):
        """ 有多个键值的话就是 AND 的关系"""
        res = BaseHandle.find_many(self.collection, data, data_field)
        return res

    def cursor2list(self, cursor, fields:dict={}, convert:dict ={}):
        ret = []
        for i in cursor:
            for to_field, from_field_type in convert.items():
                field_type = from_field_type.split('.')
                i[to_field] = eval(field_type[1])(i.pop(field_type[0]))
            for field, save in fields.items():
                if not save:
                    i.pop(field)
            ret.append(i)
        return ret

    def find_in(self, field, item_list, data_field={}):
        """SELECT * FROM inventory WHERE status in ("A", "D")"""
        data = dict()
        data[field] = {"$in": item_list}
        res = BaseHandle.find_many(self.collection, data, data_field)
        return res

    def find_or(self, data_list, data_field={}):
        """db.inventory.find(
    {"$or": [{"status": "A"}, {"qty": {"$lt": 30}}]})

        SELECT * FROM inventory WHERE status = "A" OR qty < 30
        """
        data = dict()
        data["$or"] = data_list
        res = BaseHandle.find_many(self.collection, data, data_field)
        return res

    def find_between(self, field, value1, value2, data_field={}):
        """获取俩个值中间的数据"""
        data = dict()
        data[field] = {"$gt": value1, "$lt": value2}
        # data[field] = {"$gte": value1, "$lte": value2} # <>   <= >=
        res = BaseHandle.find_many(self.collection, data, data_field)
        return res

    def find_more(self, field, value, data_field={}):
        data = dict()
        data[field] = {"$gt": value}
        res = BaseHandle.find_many(self.collection, data, data_field)
        return res

    def find_less(self, field, value, data_field={}):
        data = dict()
        data[field] = {"$lt": value}
        res = BaseHandle.find_many(self.collection, data, data_field)
        return res

    def find_like(self, field, value, data_field={}):
        """ where key like "%audio% """
        data = dict()
        data[field] = {'$regex': '.*' + value + '.*'}
        print(data)
        res = BaseHandle.find_many(self.collection, data, data_field)
        return res

    def query_limit(self, query, limit, skip=0):
        """db.collection.find(<query>).limit(<number>) 获取指定数据"""
        res = self.find_many(query).limit(limit).skip(skip)
        return res

    def query_count(self, query):
        res = self.find_many(query).count()
        return res

    def query_sort(self, query, data, data_field={}):
        """db.orders.find().sort( { amount: -1 } ) 根据amount 降序排列"""
        res = self.find_many(query, data_field).sort(data)
        return res

    def delete_one(self, data):
        """ 删除单行数据 如果有多个 则删除第一个"""
        res = BaseHandle.delete_one(self.collection, data)
        return res

    def delete_many(self, data):
        """ 删除查到的多个数据 data 是一个字典 """
        res = BaseHandle.delete_many(self.collection, data)
        return res


class NcovExpertsDB(DBBase):
    def __init__(self):
        super(NcovExpertsDB, self).__init__('ncov')


class nCovCasesDB(DBBase):
    def __init__(self):
        super(nCovCasesDB, self).__init__('nCoV_cases_data')


class nCovCasesDXYDB(DBBase):
    def __init__(self):
        super(nCovCasesDXYDB, self).__init__('nCoV_cases_dxy')


class NcovChangeLogDB(DBBase):
    def __init__(self):
        super(NcovChangeLogDB, self).__init__('nCoVpredict_change_log')



class NcovWHOWorldDB(DBBase):
    def __init__(self):
        super(NcovWHOWorldDB, self).__init__('who_COVID_19_pdf_tables_word')


class NcovInflowsDB(DBBase):
    def __init__(self):
        super(NcovInflowsDB, self).__init__('COVID_19_shurubingli_gn')


class NcovWorldPredictDB(DBBase):
    def __init__(self):
        super(NcovWorldPredictDB, self).__init__('nCov_19_world_prediction')


class CovidDatasetDB(DBBase):
    def __init__(self):
        super(CovidDatasetDB, self).__init__('COVID_dataset')


class FeedbackDB(DBBase):
    def __init__(self):
        super(FeedbackDB, self).__init__('feedback')


class COVID_KG_ZH_EN(DBBase):
    def __init__(self):
        super(COVID_KG_ZH_EN, self).__init__('COVID_KG_ZH_EN')

class COVID_KG_EN(DBBase):
    def __init__(self):
        super(COVID_KG_EN, self).__init__('COVID_KG_EN')


class COVID_KG_ZH(DBBase):
    def __init__(self):
        super(COVID_KG_ZH, self).__init__('COVID_KG_ZH')


class COVID_KG_HEAD_TAIL(DBBase):
    def __init__(self):
        super(COVID_KG_HEAD_TAIL, self).__init__('COVID_KG_HEAD_TAIL_NEW')

class ENTITY_HOT(DBBase):
    def __init__(self):
        super(ENTITY_HOT, self).__init__('Entity_Hot')

class Drop_ENTITIES(DBBase):
    def __init__(self):
        super(Drop_ENTITIES, self).__init__('Drop_entities')


class Drop_RELATIONS(DBBase):
    def __init__(self):
        super(Drop_RELATIONS, self).__init__('Drop_relations')


class Drop_ZH_KNOWLEDGE(DBBase):
    def __init__(self):
        super(Drop_ZH_KNOWLEDGE, self).__init__('Drop_zh_knowledge')

class Drop_EN_KNOWLEDGE(DBBase):
    def __init__(self):
        super(Drop_EN_KNOWLEDGE, self).__init__('Drop_en_knowledge')


class COVID_QA_relation(DBBase):
    def __init__(self):
        super(COVID_QA_relation, self).__init__('COVID_triples')


class EVENT_ENTITY(DBBase):
    def __init__(self):
        super(EVENT_ENTITY, self).__init__('EVENT_ENTITY')

class COVID_KG_WORD_EVENTS(DBBase):
    def __init__(self):
        super(COVID_KG_WORD_EVENTS, self).__init__('COVID_WORD_EVENTS')


class deficiency_QA(DBBase):
    def __init__(self):
        super(deficiency_QA, self).__init__('deficiency_QA')

class COVID_PAPERS_REFERENCE(DBBase):
    def __init__(self):
        super(COVID_PAPERS_REFERENCE, self).__init__('COVID_PAPERS_REFERENCE_DIMENSIONS_SPIDER')
