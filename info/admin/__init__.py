from flask import  Flask,Blueprint
from flask import redirect
from flask import request
from flask import session

admin_blue = Blueprint("admin",__name__,url_prefix="/admin")


from . import  views

@admin_blue.before_request
def check_admin():
    is_admin = session.get("is_admin",None)
    # 如果不是管理管理员,那么就不允许进入后台,并且不能让你访问后台的管理系统
    if not is_admin and not request.url.endswith("/admin/login"):
        # 检查当前登陆到后台的用户到底是不是管理员
        return redirect("/")

