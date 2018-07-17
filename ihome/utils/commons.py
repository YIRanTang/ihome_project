# coding:utf-8
from werkzeug.routing import BaseConverter
from flask import g, session,jsonify
from functools import wraps

from ihome.utils.response_code import RET


class RegexConverter(BaseConverter):
    def __init__(self, url_map, regex):
        super(RegexConverter, self).__init__(url_map)
        self.regex = regex


def login_required(func):
    '''检查用户的登陆状态'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")

        if user_id is not None:
            g.user_id = user_id
            return func(*args,**kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR,errmsg="用户未登录")
    return wrapper
