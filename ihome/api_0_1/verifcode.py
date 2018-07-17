# coding:utf-8
import random
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET
from ihome import redis_store, constants
from ihome.libs.yuntongxun.sms import CCP
from flask import current_app, jsonify, make_response, request
from . import api
from ihome.models.models import User


# /smscode?mobile=213213123&code=123123&codeId=d9be237c-724f-47af-8f45-7b318e62b889
# 生成短信验证码
@api.route("/smscode/<re(r'(1[34578]\d{9})'):mobile>")
def send_sms_code(mobile):
    # 接收参数 手机号，图片验证码，图片验证码编号
    image_code = request.args.get("code")  # 图片验证码
    image_code_id = request.args.get("codeId")  # 图片验证码编号

    # 校验参数
    if not all([image_code, image_code_id]):
        resp = {
            "errno": RET.PARAMERR,
            "errmsg": "参数不完整"
        }
        return jsonify(resp)
    # 业务逻辑

    # 获取redis数据库获取图片验证码
    image_code_key = "image_code_" + image_code_id
    try:
        real_image_code = redis_store.get(image_code_key)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.DBERR,
            "errmsg": "获取图片验证码失败"
        }
        return jsonify(resp)
    # 判断验证码是否失效
    if real_image_code is None:
        resp = {
            "errno": RET.NODATA,
            "errmsg": "验证码已失效"
        }
        return jsonify(resp)
    # 把图片验证码从数据库删除
    try:
        redis_store.delete(image_code_key)
    except Exception as e:
        current_app.logger.error(e)

    # 对比用户输入的验证码和真实验证码
    if real_image_code.lower() != image_code.lower():
        resp = {
            "errno": RET.DATAERR,
            "errmsg": "验证码输入错误"
        }
        return jsonify(resp)

    # 判断手机号是否被注册
    try:

        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            resp = {
                "errno": RET.DATAEXIST,
                "errmsg": "手机号码已注册"
            }
            return jsonify(resp)

    # 生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 把短信验证码存入redis数据库
    sms_code_key = "sms_code_%s" % mobile
    try:
        redis_store.setex(sms_code_key,constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.DATAERR,
            "errmsg": "保存短信验证码异常"
        }
        return jsonify(resp)
    # 发送短信验证码
    try:
        ccp = CCP()
        result = ccp.sendTemplateSMS(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.THIRDERR,
            "errmsg": "发送短信异常"
        }
        return jsonify(resp)

    # 返回
    if result==1:
        resp = {
            "errno": RET.OK,
            "errmsg": "发送短信成功"
        }
        return jsonify(resp)
    else:
        resp = {
            "errno": RET.THIRDERR,
            "errmsg": "发送短信失败"
        }
        return jsonify(resp)


# 生成图片验证码
@api.route("/image_codes/<re(r'.*'):code_id>")
def get_image_codes(code_id="123"):
    name, text, getvalue = captcha.generate_captcha()

    # 把验证码正确值写入reids
    image_code_key = "image_code_" + code_id
    try:
        redis_store.setex(image_code_key, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "error": RET.DBERR,
            "errmsg": "save image code failed"
        }
        return jsonify(resp)
    resp = make_response(getvalue)
    resp.headers["Content-Type"] = "image/jpg"
    return resp
