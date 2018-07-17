# coding:utf-8

from ihome import db, constants
from . import api
from flask import request, jsonify, current_app, g,session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models.models import User
from ihome.utils.commons import login_required


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    # 接收参数
    req_file = request.files.get("avatar")
    # 校验参数
    if req_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="请选择要上传的图片")
    # 业务逻辑
    file_data = req_file.read()
    try:
        file_name = storage(file_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片异常")

    user_id = g.user_id
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图像信息出错")
    avatar_url = constants.QINIU_USER_ACCESS_DOMAIN_URL + file_name
    # 返回
    return jsonify(errno=RET.OK, errmsg="OK", avatar_url=avatar_url)


@api.route("/users/avatar", methods=["GET"])
@login_required
def get_user_avatar():
    # 个人信息显示
    user_id = g.user_id
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="信息查询失败")

    avatar_url = constants.QINIU_USER_ACCESS_DOMAIN_URL + user.avatar_url

    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url":avatar_url, "user_name":user.name})

#
@api.route("/users/name",methods=["PUT"])
@login_required
def change_users_name():
    '''更改用户名'''
    # 接受参数
    req_dict = request.get_json()
    if not req_dict:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    user_name = req_dict.get("name")

    if not user_name:
        return jsonify(errno=RET.PARAMERR, errmsg="名字不能为空")

    # 业务逻辑
    user_id = g.user_id

    # 利用数据库存储username的唯一性
    try:
        User.query.filter_by(id=user_id).update({"name":user_name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="设置用户名错误")

    # 更该session
    session["user_name"] = user_name

    return jsonify(errno=RET.OK,errmsg="修改用户名成功",data={"name":user_name})