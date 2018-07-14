# coding:utf-8

import redis
class Config(object):
    # mysql 数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # redis 数据库
    REDIS_HOSE = "127.0.0.1"
    REDIS_PORT = "6379"

    # session 配置
    SECRET_KEY = "dsfsddfsdlfhldhfldhkfl"
    SESSION_TYPE = "redis"
    SESSION_USER_SIGNER = True
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOSE,port=REDIS_PORT)
    PERMANENT_SESSION_LEFTTIME =86400

class DevelopConfig(Config):
    DEBUG = True

class ProductConfig(Config):
    pass

config_dict = {
    "develop" : DevelopConfig,
    "product" : ProductConfig

}