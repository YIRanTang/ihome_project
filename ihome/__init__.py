# coding:utf-8


import redis,logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config_dict
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from ihome.utils.commons import RegexConverter


db = SQLAlchemy()
csrf = CSRFProtect()
redis_store = None


# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日记录器
logging.getLogger().addHandler(file_log_handler)

# flask工厂配置
def create_app(config_name):
    app = Flask(__name__)

    conf = config_dict[config_name]

    # 导入配置
    app.config.from_object(conf)

    # 延迟构造
    db.init_app(app)
    csrf.init_app(app)

    global redis_store
    redis_store = redis.StrictRedis(host=conf.REDIS_HOSE, port=conf.REDIS_PORT)

    Session(app)

    # 添加自定义路由转换器
    app.url_map.converters['re'] = RegexConverter

    from api_0_1 import api
    app.register_blueprint(api,url_prefix="/api/v1_0")

    from web_html import html
    app.register_blueprint(html)

    return app
