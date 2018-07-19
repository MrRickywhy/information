from flask import g, jsonify,redirect
from flask import  render_template
from flask import request

from info import db,constants
from info.models import Category, News, User
from info.utils.common import user_login_data
from info.utils.response_code import RET
from info.utils.image_storage import storage


from . import  profile_blue

@profile_blue.route("/other_news_list")
def other_news_list():
    page = request.args.get("p", 1)
    user_id = request.args.get("user_id")


    try:
        page = int(page)

    except Exception as e:
        page = 1

    paginate = News.query.filter(News.user_id == user_id).paginate(page, 10, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return  jsonify(errno=RET.OK, errmsg="OK", data=data)


@profile_blue.route("/other_info")
@user_login_data
def other_info():
    user = g.user
    id = request.args.get("id")
    other = User.query.get(id)

    is_followed = False
    if user:
        if other in user.followed:
            is_followed = True

    data = {
        "user_info": user.to_dict(),
        "other_info": other.to_dict(),
        "is_followed": is_followed
    }




    return render_template("news/other.html",data = data)















@profile_blue.route("/follow")
@user_login_data
def follow():
    """我的关注"""


    user = g.user
    page = request.args.get("p",1)

    try:
        page = int(page)

    except Exception as e:
        page = 1

    paginate = user.followed.paginate(page,10,False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    followed_list = []

    for item in items:
        followed_list.append(item.to_dict())


    data = {
        "users":followed_list ,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("news/user_follow.html", data=data)









@profile_blue.route("/news_list")
@user_login_data
def news_list():


    user = g.user
    page = request.args.get("p",1)

    try:
        page = int(page)

    except Exception as e:
        page = 1

    paginate = News.query.filter(News.user_id == user.id).paginate(page,3,False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_list = []

    for news in items:
        news_list.append(news.to_review_dict())


    data = {
        "news_list":news_list ,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("news/user_news_list.html", data=data)
















@profile_blue.route("/news_release",methods = ["GET","POST"])
@user_login_data
def news_release():
    """发布新闻"""
    user = g.user

    if request.method == "GET":
        categorys = Category.query.all()
        categories_dicts = []
        for category in categorys:
            categories_dicts.append(category.to_dict())
        categories_dicts.pop(0)

        return render_template("news/user_news_release.html",data ={"categories": categories_dicts})

        # 1. 获取要提交的数据
    title = request.form.get("title")
    source = "个人发布"
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image").read()
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    # 把图片存储到七牛
    index_image = storage(index_image)
    news = News()
    news.title = title
    news.source = source
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + index_image
    news.category_id = category_id
    news.user_id = user.id
    news.status = 1
    db.session.add(news)
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="ok")



@profile_blue.route("/collection")
@user_login_data
def collection():

    """
    我的收藏：
    　　１：我的收藏表示当前登陆用户的收藏，需要判断当前用户是否已经登陆
        2: 如果用户已经登陆，直接查询用户的收藏列表
    :return:
    """
    user = g.user
    page = request.args.get("p",1)

    try:
        page = int(page)

    except Exception as e:
        page = 1

    paginate = user.collection_news.paginate(page,3,False)

    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    collection_list = []

    for collection in items:

        collection_list.append(collection.to_dict())


    data = {
        "collections":collection_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("news/user_collection.html", data=data)







@profile_blue.route("/pass_info",methods = ["GET","POST"])
@user_login_data
def pass_info():
    user = g.user
    if request.method == "GET":
        return render_template("news/user_pass_info.html")
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="旧密码错误")

    user.password = new_password
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="密码修改成功")


@profile_blue.route("/pic_info",methods = ["GET","POST"])
@user_login_data
def pic_info():
    user = g.user

    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None,
        }

        return render_template("news/user_pic_info.html",data = data)
    # 获取图片文件
    avatar = request.files.get("avatar").read()
    # 上传千牛云
    key = storage(avatar)
    user.avatar_url = key
    db.session.commit()
    data = {
        "avatar_url":constants.QINIU_DOMIN_PREFIX+key
    }
    return jsonify(errno=RET.OK, errmsg="上传成功", data=data)



@profile_blue.route("/base_info",methods = ["GET","POST"])
@user_login_data
def base_info():
    user = g.user

    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None,
        }

        return render_template("news/user_base_info.html",data = data)

    nick_name = request.json.get("nick_name")
    # 获取到用户的签名
    signature = request.json.get("signature")
    # 获取到用户的性别
    gender = request.json.get("gender")

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="修改成功")


















@profile_blue.route("/info")
@user_login_data
def get_user_info():
    user = g.user
    if not user:
        return redirect("/")
    data = {
        "user_info": user.to_dict() if user else None,
    }

    return render_template("news/user.html",data = data)