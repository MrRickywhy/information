from datetime import datetime
import random

from flask import request,make_response, jsonify
from flask import session

from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET
from . import passport_blue
from info.utils.captcha.captcha import captcha
from info import redis_store, db
from info import constants
import re


"""
图片验证码验证流程
    前端页生成验证码编号，并将编号并提交到后台去请求验证码图片
    后台生成图片验证码，并把验证码文字内容当作值，验证码编号当作key存储在 redis 中
    后台把验证码图片当作响应返回给前端
    前端申请发送短信验证码的时候带上第1步验证码编号和用户输入的验证码内容
    后台取出验证码编号对应的验证码内容与前端传过来的验证码内容进行对比
    如果一样，则向指定手机发送验证码，如果不一样，则返回验证码错误
"""

@passport_blue.route("/image_code")

def get_image_code():

    code_id = request.args.get("code_id")
    name,text,image =  captcha.generate_captcha()
    resp = make_response(image)
    resp.headers['Content-Type'] = "image/jpg"
    # 保存图片验证码到redis
    redis_store.set("image_code_"+code_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)

    return resp




"""
发送短信验证码实现流程：
    接收前端发送过来的请求参数
    检查参数是否已经全部传过来
    判断手机号格式是否正确
    检查图片验证码是否正确，若不正确，则返回
    删除图片验证码
    生成随机的短信验证码
    使用第三方SDK发送短信验证码
"""


@passport_blue.route("/sms_code",methods = ["POST"])
def sms_code():
    mobile = request.json.get("mobile")
    image_code = request.json.get("image_code")
    image_code_id = request.json.get("image_code_id")
    if not all([mobile, image_code_id, image_code]):
        # 参数不全
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    if not re.match(r"1[3456789]\d{9}",mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机号不正确")
    real_image_code = redis_store.get("image_code_"+image_code_id)
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="redis已经过期")
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.PARAMERR, errmsg="请输入正确的验证码")
    # 编辑发送的短信内容
    result = random.randint(0,999999)
    sms_code_random = "%06d" % result
    # 存储短信验证码
    redis_store.set("sms_code_"+mobile,sms_code_random,constants.SMS_CODE_REDIS_EXPIRES)
    print("短信内容是："+ sms_code_random )
    statusCode = CCP().send_template_sms(mobile, [sms_code_random, 5], 1)
    if statusCode != 0:
        return jsonify(errno=RET.THIRDERR, errmsg="短信发送失败")


    return jsonify(errno=RET.OK, errmsg="成功")


"""
1. 获取参数和判断是否有值
2. 从redis中获取指定手机号对应的短信验证码的
3. 校验验证码
4. 初始化 user 模型，并设置数据并添加到数据库
5. 保存当前用户的状态
6. 返回注册的结果

"""
@passport_blue.route("/register",methods = ["POST"])
def register():
    # 获取用户注册的时候输入的手机号
    mobile = request.json.get("mobile")
    # 获取用户注册的时候输入的短信验证码
    smscode = request.json.get("smscode")
    # 获取用户注册的时候输入的密码
    password = request.json.get("password")

    if not all([mobile, smscode, password]):
        # 参数不全
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")
    real_sms_code = redis_store.get("sms_code_"+mobile)
    if not real_sms_code:
        return jsonify(RET.NODATA,errmsg = "短信验证码过期")
    if real_sms_code !=  smscode:
        return jsonify(errno=RET.PARAMERR, errmsg="请输入正确的短信验证码")
    user = User()
    user.nick_name = mobile
    user.password = password
    user.mobile = mobile
    user.last_login = datetime.now()
    db.session.add(user)
    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "注册成功")

@passport_blue.route("/login",methods = ["POST"])
def login():
    mobile = request.json.get("mobile")
    password = request.json.get("password")

    if not all([mobile, password]):
        # 参数不全
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    user = User.query.filter(User.mobile == mobile).first()
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="没有这个用户")

    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["moblie"] = user.mobile

    session["is_admin"] = user.is_admin

    user.last_login = datetime.now()
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="登陆成功")


@passport_blue.route("/logout")
def logout():
    session.pop( "user_id" ,None)
    session.pop("nick_name", None)
    session.pop("moblie", None)
    session.pop("is_admin", None)
    return jsonify(errno=RET.OK, errmsg="OK")