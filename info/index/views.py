from flask import g
from flask import request, jsonify
from flask import session

from info.models import User, News, Category
from info.utils.response_code import RET
from . import index_blue
from flask import Flask,render_template,current_app
from info.utils.common import user_login_data

@index_blue.route("/news_list")
def news_list():
    # 新闻分类id
    cid = request.args.get("cid",1)
    # 当前页面表示哪一页的数据
    page = request.args.get("page",1)
    # 每一页有多少数据
    per_page = request.args.get("per_page",10)
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        cid = 1
        page = 1
        per_page = 10
    # News.status == 0:表示审核通过,因为我们所有的新闻必须审核之后才能阅读
    filter = [News.status == 0]
    if cid != 1:
        filter.append(News.category_id == cid)
    # paginate：作用是进行分页：
    # 第一个参数：表示当前页面
    # 第二个参数：表示每个页面有多少条数据
    # 第三个参数表示没有错误输出
    # if cid == 1:
    #     paginate = News.query.order_by(News.create_time.desc()).paginate(page, per_page,False)
    #
    # else:
    paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page, per_page,
                                                                                                         False)


    # 当前页面的数据
    items = paginate.items
    # 当前页面
    current_page = paginate.page
    # 总页数
    total_page = paginate.pages

    news_list = []
    for news in items:
        news_list.append(news.to_dict())

    data = {
        "current_page": current_page,
        "total_page": total_page,
        "news_dict_li": news_list
    }

    return jsonify(errno=RET.OK, errmsg="ok", data=data)









@index_blue.route("/favicon.ico")
def favicon():

    return current_app.send_static_file("news/favicon.ico")





@index_blue.route('/')
@user_login_data
def index():
    user = g.user
    # # 从session取用户登陆的数据，
    # # user.id表示唯一标识
    # user_id = session.get("user_id")
    # # 给用户一个默认值
    # user = None
    # # 如果有数据说明用户已经登陆，如果取出来的数据为none,说明用户没有登陆
    # if user_id:
    #     user = User.query.get(user_id)
    # user = user_login_data()
    # data = {
    #     "user_info" : user.to_dict if user else None
    # }

    """右边的点击排行"""
    news_model = News.query.order_by(News.clicks.desc()).limit(10)
    news_list = []
    for news in news_model:
        news_list.append(news.to_dict())


    """新闻分类"""
    Categorys = Category.query.all()
    category_list = []

    for category in Categorys:
        category_list.append(category.to_dict())


    data ={
        "user_info": user.to_dict() if user else None,
        "click_news_list":news_list,
        "categories":category_list
    }

    # 需要把当前从数据库里面的user对象传递到前端的模板里面，在模板里面进行if判断，是否已经登陆
    return render_template("news/index.html", data = data)