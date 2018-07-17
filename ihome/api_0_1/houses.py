# coding:utf-8
import json
from flask import g, current_app, jsonify, request
from ihome import constants, db, redis_store
from ihome.models.models import User, Area, House, Facility, HouseImage
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from ihome.utils.response_code import RET
from . import api


@api.route("/houses/list", methods=["GET"])
@login_required
def get_houses_list():
    # 业务逻辑
    user_id = g.user_id

    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERRm, errmsg="获取房源异常")

    # 判断用户是否实名认证
    if user.id_card is None and user.real_name is None:
        return jsonify(errno=RET.NODATA, errmsg="用户为实名认证")

    # todo:获取房源信息
    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/areas", methods=['GET'])
def get_areas():
    '''获取城区信息'''
    # 业务逻辑
    # 从redis数据库拿取数据
    try:
        areas_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
        areas_json = None
    # 如果redis 没有数据 就去mysql获取
    if areas_json is None:

        try:
            areas_list = Area.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="城区查询异常")

        areas = []
        for area in areas_list:
            areas.append(area.to_dict())

        areas_json = json.dumps(areas)
        try:
            redis_store.setex("area_info", constants.AREA_INFO_MAX_TIME, areas_json)
        except Exception as e:
            current_app.logger.error(e)

    return '{"errno": 0, "errmsg": "查询城区信息成功", "data":{"areas": %s}}' % areas_json, 200, \
           {"Content-Type": "application/json"}


@api.route("/house/info", methods=['POST'])
@login_required
def save_house_info():
    # 获取参数、
    house_data = request.get_json()
    print house_data
    if not house_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 业务逻辑
    # 判断 押金和单价格式是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="价钱格式不正确")

    user_id = g.user_id

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 获取 房屋设施
    facility_id_list = house_data.get("facility")

    if facility_id_list:
        # 表示用户勾选了房屋设施
        try:
            facility_list = Facility.query.filter(Facility.id.in_(facility_id_list)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        # 如果设施存在
        if facility_list:
            house.facilities = facility_list

    # 保存房屋设施信息
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存房屋信息错误")

    # 返回
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"house_id": house.id})


@api.route("/house/image", methods=['POST'])
@login_required
def save_house_image():
    # 接收参数
    house_id = request.form.get("house_id")
    image_file = request.files.get("house_image")

    print house_id
    print image_file
    # 校验参数
    if not all([house_id, image_file]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 业务逻辑
    try:
        house = House.query.filter_by(id=house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.DBERR, errmsg="房屋不存在")

    # 上传图片到七牛
    house_image_data = image_file.read()
    try:
        file_name = storage(house_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片异常")

    try:
        house_image = HouseImage(house_id=house_id, url=file_name)
        db.session.add(house_image)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图像信息出错")

    if not house.index_image_url:
        # 如果为空这张图片插入在房屋表
        house.index_image_url = file_name
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="保存图像信息出错")

    house_image_url = constants.QINIU_USER_ACCESS_DOMAIN_URL + file_name
    # 返回
    return jsonify(errno=RET.OK, errmsg="OK", data={"house_image_url": house_image_url})
