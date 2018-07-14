# coding:utf-8
from flask import current_app, request, jsonify,session
from ihome.utils.response_code import RET
from . import api
from ihome import redis_store, db
from ihome.models.models import User


# /api/v1_0/users
@api.route("/users", methods=["POST"])
def register():
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
        "errno":RET.OK,
        "errmsg":"注册成功"
    }
    return jsonify(resp)