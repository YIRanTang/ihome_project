# coding:utf-8
from CCPRestSDK import REST
import ConfigParser

accountSid = '8a216da86488ce4801649338428506a4';
# 说明：主账号，登陆云通讯网站后，可在控制台首页中看到开发者主账号ACCOUNT SID。

accountToken = '0c785cc7d5984da480c94b66e1a561fc';
# 说明：主账号Token，登陆云通讯网站后，可在控制台首页中看到开发者主账号AUTH TOKEN。

appId = '8a216da86488ce480164933842de06ab';
# 请使用管理控制台中已创建应用的APPID。

serverIP = 'app.cloopen.com';
# 说明：请求地址，生产环境配置成app.cloopen.com。

serverPort = '8883';
# 说明：请求端口 ，生产环境为8883.

softVersion = '2013-12-26';  # 说明：REST API版本号保持不变。


class CCP(object):
    def __new__(cls):
        # 判断类是否有instance这个属性，有的话直接返回
        if not hasattr(cls,"instance"):
            obj = super(CCP,cls).__new__(cls)
            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj

        return cls.instance


    # 发送验证码的接口
    def sendTemplateSMS(self,to, datas, tempId):
        try:
            # 调用云通讯的工具rest发送短信
            result = self.rest.sendTemplateSMS(to, datas, tempId)
        except Exception as e:
            raise e
        status_code = result.get("statusCode")
        if status_code == "000000":
            # 发送成功
            return 1
        else:
            # 发送失败
            return 0

if __name__ == '__main__':
    ccp = CCP()
    ccp.sendTemplateSMS("18307494480",["1234",5],1)
