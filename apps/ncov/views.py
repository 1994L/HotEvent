import json
import os
import jieba

from flask_restful import Resource
from flask import current_app, request

from apps.common import Code, pretty_result, root_parser
from apps.ncov.predict import predict
from apps.ncov import interface
from apps import cache
from apps.ncov.flight_risk_v2 import flight_risk
from utils.logger import logRecord
from apps.ncov.ncov_db_opt import *


file_path = os.path.join(os.path.dirname(__file__), 'file')


class PredictView(Resource):
    def __init__(self):
        self.parser = root_parser().copy()

    @cache.cached(timeout=60*60)
    def get(self):
        args = self.parser.parse_args()
        try:
            ret = predict()
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when request /pneumonia/prediction: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class NcovDataView(Resource):
    def __init__(self):
        self.parser = root_parser().copy()
        self.type_dic = {
            0: 'china',
            1: 'world',
            2: 'inflows'
        }

    def get(self):
        '''
        type: {
            "china": 0,
            "world": 1,
            "inflows": 2
        }
        :return:
        '''
        self.parser.add_argument('type', type=int, location='args', required=False, default=0)
        args = self.parser.parse_args()
        try:
            ret = getattr(interface, f"ncov_{self.type_dic.get(args.type, 'china')}")()
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when request /pneumonia/data: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class PredictChangelogView(Resource):
    def get(self):
        try:
            ret = interface.predict_changelog()
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            current_app.logger.error(str(e))
            return pretty_result(Code.DB_ERROR)


class FlightRisk(Resource):
    '''
    航班风险预测
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        '''
        航班风险预测
        :return:
        '''
        self.parser.add_argument('flynum', type=str, location='args', required=False, default=None)
        self.parser.add_argument('area', type=str, location='args', required=False, default=None)
        args = self.parser.parse_args()
        try:
            if not args.flynum and not args.area:
                return pretty_result(Code.PARAM_ERROR)
            risk_result = flight_risk(args.flynum, args.area)
            if risk_result:
                if type(risk_result) == tuple:
                    depCity, arrCity, risk = risk_result
                    ret = {
                        'depCity': depCity,
                        'arrCity': arrCity,
                        'forcast': round(risk, 2)
                    }
                else:
                    ret = {
                        'forcast': round(risk_result, 2)
                    }
                return pretty_result(Code.OK, data=ret)
            return pretty_result(Code.CUSTOM_ERROR, msg='航班或地点暂未收录或不存在')
        except Exception as e:
            logRecord(f'when request /pneumonia/flight-risk: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class NcovDatasetsView(Resource):
    '''
    疫情数据集视图
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        '''
        获取全部数据集
        :return:
        '''
        self.parser.add_argument('sortby', type=str, location='args', required=False, default='Time')
        self.parser.add_argument('order', type=int, location='args', required=False, default=1)
        args = self.parser.parse_args()
        try:
            ret = query_all_dataset(args.sortby, args.order)
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when GET /pneumonia/dataset: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.DB_ERROR, msg=e, debug=args.debug)

    def post(self):
        '''
        新增数据集
        :return:
        '''
        self.parser.add_argument("data", type=dict, location="json", required=True)
        args = self.parser.parse_args()
        try:
            ret = add_dataset(args.data)
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when POST /pneumonia/dataset: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.DB_ERROR, msg=e, debug=args.debug)


class NcovDatasetView(Resource):

    def __init__(self):
        self.parser = root_parser().copy()

    def put(self, id):
        '''
        编辑数据集
        :return:
        '''
        self.parser.add_argument("data", type=dict, location="json", required=True)
        args = self.parser.parse_args()
        try:
            ret = edit_dataset_by_id(id, args.data)
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when PUT /pneumonia/dataset: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.DB_ERROR, msg=e, debug=args.debug)

    def delete(self, id):
        '''
        删除数据集
        :return:
        '''
        args = self.parser.parse_args()
        try:
            del_dataset_by_id(id)
            return pretty_result(Code.OK, data=[])
        except Exception as e:
            logRecord(f'when DELETE /pneumonia/dataset: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.DB_ERROR, msg=e, debug=args.debug)


class FeedBackView(Resource):
    '''
    数据反馈
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('cla', type=str, location='args', required=False, default='Covid19_Datasets_dingYue')
        self.parser.add_argument('sortby', type=str, location='args', required=False, default='date')
        self.parser.add_argument('order', type=int, location='args', required=False, default=-1)
        args = self.parser.parse_args()
        try:
            ret = query_feedback(args.cla, args.sortby, args.order)
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when GET /feedback: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.DB_ERROR, msg=e, debug=args.debug)


class FeedBackOptView(Resource):
    '''
    数据反馈
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def put(self, id):
        '''
        修改反馈数据状态
        {
            0: 确认,
            1: 删除,
            2: 取消确认,
            3: 取消删除
        }
        :param id: 反馈数据id
        :return:
        '''
        self.parser.add_argument('option', type=int, location='json', required=False, default=0)
        args = self.parser.parse_args()
        try:
            ret = edit_feedback(id, args.option)
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when PUT /feedback: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.DB_ERROR, msg=e, debug=args.debug)


class EntityLinkingView(Resource):
    '''
    实体链接
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('news', type=str, location='args', trim=True)
        args = self.parser.parse_args()
        try:
            ret = interface.get_answer(args.news)
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when PUT /pneumonia/entitylink: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class EntityView(Resource):
    '''
    实体关系获取
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('url',type=str, location='args', required=True, trim=True)
        self.parser.add_argument('lang',type=str, location='args', required=True, trim=True)
        args = self.parser.parse_args()
        try:
            entity_relation = interface.get_entity_relation(args.url, args.lang)
            return pretty_result(Code.OK, data=entity_relation)
        except Exception as e:
            logRecord(f'when GET /pneumonia/entity: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)

class EntityQueryView(Resource):
    '''
    实体查询
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('entity', type=str, location='args', required=True, trim=True)
        self.parser.add_argument('mini', type=int, location='args', default=0)
        args = self.parser.parse_args()
        try:

            entity_result = interface.query_entity(args.entity, args.mini)
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/entityquery: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)

class UpdateHot(Resource):
    '''
    实体查询热度更新
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('url', type=str, location='args', required=True, trim=True)
        args = self.parser.parse_args()
        try:

            entity_result = interface.update_hot(args.url)
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/view: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)

class LenovoEntity(Resource):
    '''
    实体联想
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('name', type=str, location='args', required=True, trim=True)
        args = self.parser.parse_args()
        try:

            entity_result = interface.lenovo_entity(args.name)
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/hit: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class Downloads(Resource):
    '''
    下载未标注数据
    '''
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('nums', type=int, location='args', default=0)
        args = self.parser.parse_args()
        try:
            data_path = f'{file_path}/entities_labeled.xls'
            entity_result = interface.downloads(data_path, args.nums)
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/hit: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class Renewal(Resource):
    '''
    上传已标注数据，并更新到数据库
    '''

    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('nums', type=int, location='args', default=0)
        args = self.parser.parse_args()
        try:
            data_path = f'{file_path}/entities_labeled.xls'
            entity_result = interface.update_mongo(data_path, file_path)
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/hit: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class QA_Answer(Resource):
    '''
    entity和relation问答
    '''

    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('entity', type=str, required=True, trim=True, location='args')
        self.parser.add_argument('relation', type=str, required=True, trim=True, location='args')
        args = self.parser.parse_args()
        try:
            entity_result = interface.QA_answers(args.entity, args.relation)
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/hit: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class Show_Update(Resource):
    '''
    展示更新
    '''

    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        args = self.parser.parse_args()
        try:
            entity_result = interface.show_update()
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/hit: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)

class QA(Resource):
    '''
    上传已标注数据，并更新到数据库
    '''

    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument('question', type=str, required=True, trim=True, location='args')
        args = self.parser.parse_args()
        try:
            entity_result = interface.QA(args.question)
            return pretty_result(Code.OK, data=entity_result)
        except Exception as e:
            logRecord(f'when GET /pneumonia/hit: {str(e)}', level='error', debug=args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)

