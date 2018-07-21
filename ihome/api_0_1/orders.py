# coding:utf-8
from flask import g, current_app, jsonify, request
from ihome import db,redis_store
from ihome.models.models import House, Order
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from . import api
from datetime import datetime


@api.route("/order", methods=["post"])
@login_required
def save_order():
    # 接收参数
    req_data = request.get_json()
    house_id = req_data.get("house_id")
    start_date_str = req_data.get("start_date")
    end_date_str = req_data.get("end_date")

    user_id = g.user_id

    # 校验参数
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        # 判断时间格式
        print start_date
        print end_date
        assert end_date >= start_date
        days = (end_date - start_date).days + 1

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 判断有没有这个房子
    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="没有这个房源")

    # 判断这房子是否是房东的
    if house.user_id == user_id:
        return jsonify(errno=RET.NODATA, errmsg="不能预定自己的房子")

    try:
        # 查询冲突的房间
        count = Order.query.filter(Order.house_id == house_id, Order.end_date >= start_date,
                                   Order.begin_date <= end_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if count > 0:
        return jsonify(errno=RET.DBERR, errmsg="房间已被预定")

    amount = house.price * days

    order = Order()
    order.house_id = house_id
    order.user_id = user_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = amount

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

    return jsonify(errno=RET.OK, errmsg="OK")


# /api/v1_0/user/orders?role=custom  房客   role=landlord 房东
@api.route("/user/orders")
@login_required
def get_user_orders():
    '''订单处理'''
    user_id = g.user_id

    role = request.args.get("role", "")

    if not role:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        if role == "landlord":
            # 表示当前是房东查询订单

            # 查询出属于房东的所有房子
            houses = House.query.filter_by(user_id=user_id).all()

            house_ids = [house.id for house in houses]

            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time.desc()).all()

        else:
            # 表示当前以房客的身份查询订单
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单失败")

    order_list = [order.to_dict() for order in orders]

    return jsonify(errno=RET.OK, errmsg="查询成功", data={"orders": order_list})


# /api/v1_0/orders/"+orderId+"/status action="accept"接单 action="reject"拒单
@api.route("/orders/<int:orderId>/status", methods=["PUT"])
@login_required
def accept_reject_order(orderId):
    '''接单,拒单'''
    user_id = g.user_id
    req_data = request.get_json()
    action = req_data.get("action")

    if not action:
        return jsonify(errno=RET.PARAMERR, errsg="参数错误")

    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errsg="参数错误")

    try:
        order = Order.query.filter(Order.id == orderId).first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errsg="查询订单错误")

    # 确保订单存在且房东只能修改自己房子的订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.ROLEERR, errsg="操作无效")

    if action == "accept":
        # 接单
        order.status = "WAIT_PAYMENT"
    else:
        # 拒单
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errsg="缺少拒单理由")

        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR, errsg="操作失败")

    return jsonify(errno=RET.OK, errsg="操作成功")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    user_id = g.user_id

    req_data = request.get_json()

    comment = req_data.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
       current_app.logger.error(e)
       return jsonify(errno=RET.DATAERR, errmsg="无法获取订单数据")

    if not order:
        return jsonify(errno=RET.NODATA, errmsg="操作无效")

    try:
        # 将订单的状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的完成订单数增加1
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    # 讲redis数据库存着的房屋详情信息缓存清楚，将评论信息更新进去
    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK,errmsg="OK")