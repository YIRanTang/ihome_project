# coding:utf-8
from flask import Blueprint,make_response,current_app
from flask_wtf.csrf import generate_csrf

html = Blueprint("html",__name__)


@html.route("/<re(r'.*'):file_name>")
def get_html_file(file_name):
    if not file_name:
        file_name = "index.html"
    if file_name != "favicon.ico":
        file_name = "html/" + file_name

    # 设置csrf
    csrf_token = generate_csrf()
    print file_name
    resp = make_response(current_app.send_static_file(file_name))
    # 把csrf_token的值设置到 cookie
    resp.set_cookie("csrf_token",csrf_token)

    return resp