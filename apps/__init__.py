import os
import flask_restful
from flask import Flask, current_app, request, abort
from flask_caching import Cache
from flask_cors import *

from config import config
import logging

from logging.handlers import RotatingFileHandler
from apps.common import Code, pretty_result


def custom_abord(http_status_code, *args, **kwargs):
    # 只要http_status_code 为400， 报参数错误
    if http_status_code == 400:
        abort(pretty_result(code=Code.PARAM_ERROR))
    # 正常返回消息
    return abort(http_status_code)

# 把flask_restful中的abort方法改为我们自己定义的方法
flask_restful.abort = custom_abord


def _access_control(response):
    """
    解决跨域请求
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,HEAD,PUT,PATCH,POST,DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Max-Age'] = 86400
    return response

def _received_request():
    current_app.logger.info(f'IP: {request.remote_addr} URL: {request.path} STATUS: received')

def _finished_request(response):
    current_app.logger.info(f'IP: {request.remote_addr} URL: {request.path} STATUS: finished')
    return response


def register_logging_api(app):
    logdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    app.logger.name = 'api'
    formatter = logging.Formatter(
        '[%(levelname)s %(asctime)s %(filename)s:%(lineno)s] - %(message)s')
    handler = RotatingFileHandler(f"{logdir}/api.log", maxBytes=1024 * 1024 * 100, backupCount=10)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    # app.logger.addHandler(handler)
    logging.getLogger().addHandler(handler)


# def register_logging_flask():
#     """配置日志"""
#     # 设置日志的记录等级
#     logging.basicConfig(level=logging.DEBUG)  # 调试debug级
#     # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
#     file_log_handler = RotatingFileHandler("flask.log", maxBytes=1024 * 1024 * 100, backupCount=10)
#     # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
#     formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
#     # 为刚创建的日志记录器设置日志记录格式
#     file_log_handler.setFormatter(formatter)
#     # 为全局的日志工具对象（flask app使用的）添加日志记录器
#     logging.getLogger().addHandler(file_log_handler)

def create_app(config_name):
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config.from_object(config[config_name])
    register_logging_api(app)
    app.before_request(_received_request)
    app.after_request(_finished_request)
    # app.after_request(_access_control)


    # from apps.routes import api_v1
    # app.register_blueprint(api_v1, url_prefix='/api/v1')

    return app


app = create_app(os.getenv('FLASK_CONFIG', 'development'))
cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_HOST': '127.0.0.1', 'CACHE_REDIS_PORT': 6379, 'CACHE_REDIS_DB': '2', 'CACHE_REDIS_PASSWORD': ''})