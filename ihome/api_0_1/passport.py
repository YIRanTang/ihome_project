# coding:utf-8
import re
from flask import current_app, request, jsonify, session
from ihome.utils.response_code import RET
from . import api
from ihome import redis_store, db
from ihome.models.models import User
from ihome import constants



# /api/v1_0/users
# 注册
@api.route("/users", methods=["POST"])
def register():
    '''注册'''

    # 接收参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    phonecode = req_dict.get("phoneCode")
    password = req_dict.get("password")

    # 校验参数
    if not all([mobile, phonecode, password]):
        resp = {
            "errno": RET.PARAMERR,
            "errmsg": "参数不完整"
        }
        return jsonify(resp)

    # 业务处理

    # 从redis数据库把短信验证码取出
    sms_code_key = "sms_code_%s" % mobile
    try:
        real_sms_code = redis_store.get(sms_code_key)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.DBERR,
            "errmsg": "获取图片验证码失败"
        }
        return jsonify(resp)

    # 判断验证码是否失效
    if real_sms_code is None:
        resp = {
            "errno": RET.NODATA,
            "errmsg": "验证码已失效"
        }
        return jsonify(resp)

    # 对比用户输入的验证码和真实验证码
    if real_sms_code != real_sms_code:
        resp = {
            "errno": RET.DATAERR,
            "errmsg": "验证码输入错误"
        }
        return jsonify(resp)

    # 把短信验证码从数据库删除
    try:
        redis_store.delete(real_sms_code)
    except Exception as e:
        current_app.logger.error(e)

    # 判断手机号是否被注册
    # try:
    #     user = User.query.filter_by(mobile=mobile).frist()
    # except Exception as e:
    #     current_app.logger.error(e)
    # else:
    #     if user is not None:
    #         resp = {
    #             "errno": RET.DATAEXIST,
    #             "errmsg": "手机号码已注册"
    #         }
    #         return jsonify(resp)
    user = User(name=mobile, mobile=mobile)

    # 用户加密 对于密码的设置，调用方法属性，进行对密码加密设置
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        # 表示已经被注册
        resp = {
            "errno": RET.DATAEXIST,
            "errmsg": "手机号码已注册"
        }
        return jsonify(resp)

    # 记录用户登陆状态
    session["user_name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id

    # 返回
    resp = {
        "errno": RET.OK,
        "errmsg": "注册成功"
    }
    return jsonify(resp)


@api.route("/sessions", methods=["POST"])
def login():
    '''登陆'''

    # 获取参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")
    # 业务逻辑
    user_ip = request.remote_addr

    try:
        # 获取登陆失败的次数
        access_count = redis_store.get("access_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    print access_count
    if access_count is not None and int(access_count) >= constants.ACCESS_LOGIN_MAX_NUM:
        return jsonify(errno=RET.REQERR, errmsg="登陆过于频繁")

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息异常")
    # 判断用户名密码
    if user is None or not user.chek_password(password):
        try:
            # 账号密码错误时，自增1
            redis_store.incr("access_%s" % user_ip)
            # 设置过期时间
            redis_store.expire("access_%s" % user_ip, constants.ACCESS_LOGIN_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.PARAMERR, errmsg="用户名或密码错误")
    try:
        # 清除redis错误时登陆次数
        redis_store.delete("access_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    # 登陆成功
    # 记录用户会话消息
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_mobile"] = user.mobile
    # 返回
    return jsonify(errno=RET.OK, errmsg="登陆成功")


# 检查用户是否登陆
@api.route("/session", methods=["GET"])
def is_login():
    '''获取用户信息'''
    user_name = session.get("user_name")
    # 判断user_name是否为None,为None则未登录
    if user_name is None:
        return jsonify(errno=RET.SESSIONERR, errmsg=False)
    else:
        return jsonify(errno=RET.OK, errmsg=True, name=user_name)


# 注销/退出登陆
@api.route("/session", methods=["DELETE"])
def logout():
    '''登出'''
    # 清楚用户会话消息
    session.clear()
    return jsonify(errno=RET.OK, errmsg="OK")
