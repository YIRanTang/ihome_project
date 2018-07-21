# coding:utf-8

from ihome.tasks.main import app
from ihome.libs.yuntongxun.sms import CCP

@app.task
# 发送验证码的接口
def sendTemplateSMS(to, datas, tempId):

    ccp = CCP()
    ret = ccp.sendTemplateSMS(to, datas, tempId)
    return ret