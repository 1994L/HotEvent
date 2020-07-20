# -*- coding: utf-8 -*-
import hashlib
import json
from datetime import datetime, date
from bson import ObjectId
from flask_restful import reqparse

from .code import Code


class CJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def pretty_result(code, msg=None, data=None, debug=0):
    if msg is None:
        msg = Code.msg.get(code)
    elif isinstance(msg, Exception):
        if debug:
            msg = str(msg)
        else:
            msg = Code.msg.get(code)
    ret = json.dumps({
        'code': code,
        'msg': msg,
        'data': data
    }, ensure_ascii=False, cls=CJsonEncoder)
    return json.loads(ret)


def root_parser():
    parser_root = reqparse.RequestParser()
    parser_root.add_argument("debug", type=int, location="headers", required=False, trim=True, default=0)
    return parser_root


def hash_md5(data):
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()






