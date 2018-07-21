# coding:utf-8
import os
from flask import g, current_app, jsonify, request
from ihome import db
from ihome.models.models import House, Order
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from alipay import AliPay
from . import api
from datetime import datetime


# /api/v1_0/orders/2/payment
@api.route("/orders/<int:order_id>/payment", methods=["post"])
@login_required
def generate_order_payment(order_id):
    '''生成支付宝的支付信息'''
    user_id = g.user_id
    try:
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_PAYMENT",
                                   Order.user_id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="查询订单出错")

    if not order:
        return jsonify(errno=RET.NODATA, errmsg="此订单无效")

    # 构造支付宝的工具对象
    alipay_client = AliPay(
        appid=current_app.config.get("ALIPAY_APPID"),
        app_notify_url=None,  # 默认支付宝通知url
        app_private_key_path=os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem"),
        alipay_public_key_path=os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem"),
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False, 如果是沙箱模式，debug=True
    )

    # 向支付宝发起手机网站支付的请求
    # 手机网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string

    order_string = alipay_client.api_alipay_trade_wap_pay(
        out_trade_no=order_id,  # 我们自己的订单编号
        total_amount=str(order.amount / 100.0),  # 订单总金额
        subject=u"爱家租房-%s" % order_id,  # 展示给用户的订单信息
        return_url="http://127.0.0.1:5000/payComplete.html",  # 支付完成后跳转回的页面路径
        notify_url=None
    )

    alipay_url = current_app.config.get("ALIPAY_APPID") + "?" + order_string
    return jsonify(errno=RET.OK, errmsg="OK", data={"alipay_url": alipay_url})


@api.route("/payment", methods=["post"])
def save_payment_result():
    payment_dict = request.form.to_dict()

    if not payment_dict:
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        # 构造支付宝的工具对象
    alipay_client = AliPay(
        appid=current_app.config.get("ALIPAY_APPID"),
        app_notify_url=None,  # 默认支付宝通知url
        app_private_key_path=os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem"),
        alipay_public_key_path=os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem"),
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False, 如果是沙箱模式，debug=True
    )

    sign = payment_dict.pop("sign")
    # 判断参数是否是有支付宝构造
    # 如果返回True，表示校验成功，参数是支付宝构造的，否则为假
    result = alipay_client.verify(payment_dict, sign)

    if result:
        order_id = payment_dict.get("out_trade_no")  # 我们自己的订单编号
        trade_no = payment_dict.get("trade_no")  # 支付宝的交易编号

        # 修改数据库的数据，变更订单状态
        try:
            Order.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="记录支付结果异常")

    return jsonify(errno=RET.OK, errmsg="OK")
