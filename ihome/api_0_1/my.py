# coding:utf-8

from flask import g, current_app, jsonify, request
from ihome import constants, db
from ihome.models.models import User
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from . import api


@api.route("/users/user_info", methods=["GET"])
@login_required
def get_user_info():
    '''个人信息'''
    user_id = g.user_id
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="信息查询失败")

    avatar_url = constants.QINIU_USER_ACCESS_DOMAIN_URL + user.avatar_url
    data = {
        "avatar_url": user.avatar_url,
        "user_mobile": user.mobile,
        "user_name": user.name
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
    '''保存实名认证信息'''
    # 接收参数
    req_dict = request.get_json()

    if not req_dict:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    real_name = req_dict.get("real_name")
    id_card = req_dict.get("id_card")

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")


    #todo:验证身份证的格式
    # 业务逻辑
    user_id = g.user_id
    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None) \
            .update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        # 如果保存出错，说明数据库已存在
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存实名认证异常")

    return jsonify(errno=RET.OK, errmsg="实名认证成功！")


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    '''获取实名认证信息'''
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询实名信息异常")
    if user is None:
        # 如果为空
        return jsonify(errno=RET.DATAEXIST, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())
