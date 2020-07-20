# -*- coding: utf-8 -*-
# @Author: SPing
# @Date: 2020-03-11

import os


class Config:
    # CACHE_TYPE = 'redis',
    # CACHE_REDIS_HOST = '127.0.0.1',
    # CACHE_REDIS_PORT = 6379,
    # CACHE_REDIS_DB = '2',
    # CACHE_REDIS_PASSWORD = ''

    FLATPAGES_AUTO_RELOAD = True
    FLATPAGES_EXTENSION = '.md'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'can you guess it'
    DEFAULT_HTTP_TIMEOUT = 10
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    MONGO_ONLINE = {
        'name': 'online',
        'host': '117.119.77.139',
        'port': 30019,
        'db_name': 'eitools',
        'user': 'kegger_eitools',
        'password': 'datiantian123!@#',
        'authdb': 'eitools'
    }
    MONGO_LOCAL = {
        'name': 'local',
        'host': 'localhost',
        'port': 27017,
        'db_name': 'predictor',
        'user': '',
        'password': '',
        'authdb': ''
    }
    MONGO_CONFIG_DIC = {
        'local': MONGO_LOCAL,
        'online': MONGO_ONLINE
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """开发环境配置
    """
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8082
    WORKERS = 1
    MONGO_CONFIG = Config.MONGO_CONFIG_DIC['online']


class TestConfig(Config):
    """测试环境配置
    """


class ProductionConfig(Config):
    """生产环境
    """
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 19542
    WORKERS = 3
    MONGO_CONFIG = Config.MONGO_CONFIG_DIC['online']


# 设置配置映射
config = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
    'test': TestConfig,
    'default': DevelopmentConfig
}
