# coding:utf-8
# 常量
IMAGE_CODE_REDIS_EXPIRES = 120  # 图片验证码redis保存的有效期，单位秒

SMS_CODE_REDIS_EXPIRES = 300  # 短信验证码redis保存的有效期，单位秒

ACCESS_LOGIN_TIME = 600 # 登陆禁止时间 ，单位秒

ACCESS_LOGIN_MAX_NUM = 5 # 登陆错误5次时禁止登陆


QINIU_USER_ACCESS_DOMAIN_URL = "http://p7kohmjxl.bkt.clouddn.com/"  # 七牛云存储域名

AREA_INFO_MAX_TIME = 600 # 地区缓存最大有效时间 单位 秒