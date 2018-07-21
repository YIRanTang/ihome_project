# coding:utf-8

from celery import Celery
from ihome.tasks import config

app = Celery("ihome")

# 加载配置文件
app.config_from_object(config)

# celery自动找到任务
app.autodiscover_tasks(["ihome.tasks.sms"])
