# coding:utf-8
import json
from flask import g, current_app, jsonify, request, session
from ihome import constants, db, redis_store
from ihome.models.models import User, Area, House, Facility, HouseImage, Order
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from ihome.utils.response_code import RET
from . import api
from datetime import datetime


@api.route("/houses/list", methods=["GET"])
@login_required
def get_houses_list():
    '''获取我的房源列表'''
    # 业务逻辑
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房源异常")

    # 判断用户是否实名认证
    if user.id_card is None and user.real_name is None:
        return jsonify(errno=RET.NODATA, errmsg="用户为实名认证")

    houses_list = []
    for house in houses:
        houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


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


@api.route("/houses/index", methods=["GET"])
def get_houses_index():
    '''首页'''
    # 先从redis数据库尝试获取数据
    try:
        house_data = redis_store.get("index_houses")
    except Exception as e:
        current_app.logger.error(e)
        house_data = None

    if house_data:
        return '{"errno":0, "errmsg":"OK", "data":%s}' % house_data, 200, \
               {"Content-Type": "application/json"}
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(constants.HOUSES_INDEX_MAX)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据出错")

    if not houses:
        return jsonify(errno=RET.NODATA, errmsg="查询无数据")

    house_list = []
    for house in houses:
        if not house.index_image_url:
            continue
        house_list.append(house.to_basic_dict())

    house_data = json.dumps(house_list)
    # 存入redis数据库
    try:
        redis_store.setex("index_houses", constants.INDEX_HOUSES_MAX_TIME, house_data)
    except Exception as e:
        current_app.logger.error(e)

    return '{"errno":0, "errmsg":"OK", "data":%s}' % house_data, 200, \
           {"Content-Type": "application/json"}


@api.route("/house/detail")
def get_house_detail():
    # 查出当前浏览的用户
    user_id = session.get("user_id", "-1")

    # 接收
    house_id = request.args.get("house_id")

    # 尝试从redis数据库获取数据
    try:
        house_info = redis_store.get("house_infi_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        house_info = None
    if house_info:
        resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, house_info), 200, \
               {"Content-Type": "application/json"}
        return resp
    # 校验
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 数据库查询
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据出错")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    house_info = json.dumps(house.to_full_dict())
    try:
        redis_store.setex("house_infi_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, house_info)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, house_info), 200, \
           {"Content-Type": "application/json"}

    return resp


@api.route("/house/search")
def get_house_list():
    # 获取参数
    sd_str = request.args.get("sd", "")
    ed_str = request.args.get("ed", "")
    aid = request.args.get("aid", "")
    sk = request.args.get("sk", "new")
    page = request.args.get("p", 1)

    # 校验参数
    # 判断日期
    try:
        sd = None
        if sd_str:
            sd = datetime.strptime(sd_str, "%Y-%m-%d")

        ed = None
        if ed_str:
            ed = datetime.strptime(ed_str, "%Y-%m-%d")

        if sd and ed:
            assert ed >= sd
    except Exception as e:
        print sd_str
        print ed_str
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期错误")

    # 判断页数
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # 尝试从redis 数据库获取数据
    redis_key = "houses_%s_%s_%s_%s" % (sd_str, ed_str, aid, sk)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
        resp_json = None

    if resp_json:
        # 表示获取到了数据
        return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据
    filter_params = []

    # 把地区条件放入查询条件
    if aid:
        filter_params.append(House.area_id == aid)

    # 先查询于订单不冲突的房间
    # todo:时间判断错误
    try:
        orders = []
        if sd and ed:
            orders = Order.query.filter(Order.begin_date <= ed, Order.end_date >= sd).all()
        elif sd:
            orders = Order.query.filter(Order.end_date >= sd, Order.begin_date <= sd).all()
        elif ed:
            orders = Order.query.filter(Order.end_date >= ed, Order.begin_date <= ed).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if orders:
        house_ids = [order.house_id for order in orders]
        # 把不冲突的订单放入查询条件
        filter_params.append(House.id.notin_(house_ids))

    # 排序
    if sk == "new":
        house_quert = House.query.filter(*filter_params).order_by(House.create_time.desc())
    elif sk == "booking":
        house_quert = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sk == "price-inc":
        house_quert = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sk == "price-des":
        house_quert = House.query.filter(*filter_params).order_by(House.price.desc())

    try:
        # 分页
        houses_page = house_quert.paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 当前页的所有数据
    house_items = houses_page.items
    # 总条目数
    tatol_count = houses_page.total
    # 总页数
    tatol_page = houses_page.pages

    houses = [house_item.to_basic_dict() for house_item in house_items]

    resp = dict(errno=RET.OK, errmsg="查询成功",
                data={"tatol_count": tatol_count, "tatol_page": tatol_page, "houses": houses})
    resp_json = json.dumps(resp)

    # 将json后的数据存如ｒｅｄｉｓ数据库
    if page <= tatol_page:
        # 如果总页数大于当前页则存入数据库
        try:
            pipeline = redis_store.pipeline()
            # 开启redis事务
            pipeline.multi()
            pipeline.hset(redis_key, resp_json, page)
            pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_EXPIRES)
            # 提交事务
            pipeline.execute()
        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}

@api.route("/order/house")
@login_required
def order_house():
    house_id = request.args.get("house_id")

    if not house_id:
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    return jsonify(errno=RET.OK,errmsg="查询成功！",data=house.to_basic_dict())










