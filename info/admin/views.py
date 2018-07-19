from datetime import datetime,timedelta

from flask import g, jsonify
from flask import session
from info.utils.image_storage import  storage
from info import constants
from info import db
from info.utils.common import  user_login_data
from info.models import User, News, Category
from info.utils.response_code import RET
from . import  admin_blue
from flask import render_template,request,redirect,url_for
import  time


@admin_blue.route("/add_category",methods = ["POST"])
def add_category():
    """增加和修改分类"""

    # 表示分类id
    id = request.json.get("id")
    name = request.json.get("name")

    if id:
        # 如果有id说明,小编想修改,分类的名字
        category = Category.query.get(id)
        category.name = name
        db.session.commit()

    else:
        # 如果没有id说明,小编想增加,分类的名字
        category=Category()
        category.name = name
        db.session.add(category)
        db.session.commit()


    return jsonify(errno=RET.OK, errmsg="OK")












@admin_blue.route("/news_type")
def news_type():
    """新闻分类"""
    categorys = Category.query.all()
    category_list = []
    for category in categorys:
        category_list.append(category.to_dict())

    category_list.pop(0)
    data = {
        "categories":category_list
    }



    return render_template("admin/news_type.html",data = data)












@admin_blue.route("/news_edit_detail",methods = ["GET","POST"])
def news_edit_detail():
    """新闻版式编辑"""

    if request.method == "GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)
        categorys = Category.query.all()
        category_list = []
        for category in categorys:
            category_list.append(category)

        category_list.pop(0)

        data  = {
            "news":news.to_dict(),
            "categories":category_list
        }


        return render_template("admin/news_edit_detail.html",data = data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image").read()
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    index_image = storage(index_image)

    news = News.query.get(news_id)
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + index_image
    news.content = content
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="ok")












@admin_blue.route("/news_edit")
def news_edit():
    page = request.args.get("p", 1)

    try:
        page = int(page)

    except Exception as e:
        page = 1

    paginate = News.query.order_by(News.create_time.desc()).paginate(page, 10, False)
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

    return render_template("admin/news_edit.html",data = data)


@admin_blue.route("/news_review_detail",methods = ["GET","POST"])
def news_review_detail():
    """审核提交"""
    if request.method == "GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)
        data = {
            "news":news.to_dict()
        }



        return  render_template("admin/news_review_detail.html",data = data)

    action = request.json.get("action")
    news_id = request.json.get("news_id")
    # 暂时不需要拿这个参数,因为只有当真正拒绝的时候,才需要给原因
    # reason = request.json.get("reason")
    news = News.query.get(news_id)

    if action=="accept":
        # 表示审核通过
        news.status=0

    else:
        # 审核不通过, 如果审核不通过,就需要说明不通过的原因
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno = RET.PARAMERR,errmsg = "不通过的原因")
        news.status=-1
        news.reason = reason
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="ok")


@admin_blue.route("/news_review")
def news_review():
    """
   新闻审核:
   1 这个里面查询的是所有作者发布的新闻,在查询的时候,既然是审核页面,
     那么肯定都是没有通过审核,或者审核中的页面,那么就需要把news.status != 0过滤
   2 新闻审核页面也需要进行分页
   3 通过新闻的标题进行搜索News.title.是否包含当前新闻的关键字,所有的新闻

   """

    page = request.args.get("p", 1)
    keywords = request.args.get("keywords")


    try:
        page = int(page)

    except Exception as e:
        page = 1

    filter = [News.status!=0]

    # 小编通过关键字进行搜索的时候,不可能每次都会搜索关键字,所以,需要判断是否有关键字,有关键字才搜索,没有就不需要添加到数据库查询
    if keywords:
        filter.append(News.title.contains(keywords))

    paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page, 10, False)
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

    return render_template("admin/news_review.html", data=data)


@admin_blue.route("/user_list")
def user_list():
    """用户列表"""
    page = request.args.get("p",1)

    try:
        page = int(page)

    except Exception as e:
        page = 1

    """
    查询用户列表:查询当前网站一共有多少个用户:
    1 :如果查询用户,第一需要把小编去掉 User.is_admin = false
    2 :因为查询用户需要进行分页,所以需用用到paginate
    """
    paginate = User.query.filter(User.is_admin==False).paginate(page,10,False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    user_list = []
    for user in items:
        user_list.append(user.to_admin_dict())


    data = {
        "users":user_list,
        "current_page":current_page,
        "total_page":total_page
    }

    return  render_template("admin/user_list.html",data = data)



@admin_blue.route("/user_count",methods=["GET","POST"])
def user_count():
    # 当前的总人数
    total_count = 0
    # 每个月新增人数
    mon_count = 0
    # 每天新增人数
    day_count = 0
    # 管理员是公司员工，不算是用户，所以需要去掉
    total_count = User.query.filter(User.is_admin==False).count()
    # 获取到本地时间
    t = time.localtime()

    mon_time = "%d-%02d-01" % (t.tm_year,t.tm_mon)
    mon_time_begin = datetime.strptime(mon_time,"%Y-%m-%d")

    mon_count = User.query.filter(User.is_admin==False,User.create_time>mon_time_begin).count()
    # 计算今天的时间
    t = time.localtime()
    day_time = "%d-%02d-%02d" % (t.tm_year, t.tm_mon,t.tm_mday)
    day_time_begin = datetime.strptime(day_time, "%Y-%m-%d")

    day_count = User.query.filter(User.is_admin == False, User.create_time > day_time_begin).count()
    """
    过去一个月,每天的用户新增量

    """
    active_time = []
    active_count = []


    t = time.localtime()
    day_begin = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    day__begin_date = datetime.strptime(day_begin, "%Y-%m-%d")
    for i in range(0,31):
        begin_date = day__begin_date -timedelta(days=i)
        end_date = day__begin_date - timedelta(days=(i-1))
        count = User.query.filter(User.is_admin == False, User.create_time > begin_date,User.create_time<end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime("%Y-%m-%d"))
    active_count.reverse()
    active_time.reverse()

    data = {

        "total_count" : total_count,
        "mon_count" :mon_count,
        "day_count" :day_count,
        "active_count": active_count,
        "active_date": active_time
    }




    return render_template("admin/user_count.html",data = data)



@admin_blue.route("/index")
@user_login_data
def admin_index():
    user = g.user

    data = {
        "user":user.to_dict() if user else None
    }

    return render_template("admin/index.html",data = data )



@admin_blue.route("/login",methods = ["GET","POST"])
def admin_login():

    if request.method == "GET":
        # 判断当前登陆的用户是否是管理员，并且已经登陆，这样就可以不需要重复登陆
        is_admin = session.get("is_admin",None)
        user_id = session.get("user_id",None)
        if user_id and is_admin:
            return redirect(url_for("admin.admin_index"))


        return render_template("admin/login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    user = User.query.filter(User.mobile == username,User.is_admin==True).first()
    if not user:
        return render_template("admin/login.html",errmsg = "没有这个用户")

    if not user.check_password(password):
        return render_template("admin/login.html",errmag = "密码错误")

    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name
    session["is_admin"] = user.is_admin

    return redirect(url_for("admin.admin_index"))