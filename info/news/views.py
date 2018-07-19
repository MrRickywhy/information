from flask import g, jsonify
from flask import request
from flask import session

from info import db
from info.models import User, News, Comment, CommentLike
from info.utils.response_code import RET
from . import  news_blue
from  flask import render_template,Flask
from info.utils.common import user_login_data







@news_blue.route("/followed_user",methods=["POST"])
@user_login_data
def followes_user():

    user = g.user
    # 被关注的那个人的id(新闻作者的id)
    user_id = request.json.get("user_id")
    action = request.json.get("action")


    #查询被关注的那个人
    other = User.query.get(user_id)


    if action == "follow":
        # 说明关注,关注的前提是,我之前没有关注过你,现在才可以关注,如果之前已经关注了,那么现在就不可以关注
        if other not in user.followed:
            user.followed.append(other)

        else:
            return jsonify(errno=RET.NODATA, errmsg="已经关注了")
    else:
        if other in user.followed:
            user.followed.remove(other)

        else:
            # 说明想取消关注,如果想取消关注,前提条件是之前已经关注了,才能取消,如果之前没有关注,那说明就不需要取消
            return jsonify(errno=RET.NODATA, errmsg="没有关注")

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="OK")












@news_blue.route("/comment_like",methods=["POST"])
@user_login_data
def comment_like():
    """点赞"""
    user = g.user
    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    """
    评论点赞：
    １　评论点赞都是用户进行点赞，所以首先判断用户是否已经登陆
    ２　在进行点赞的时候，那么这条评论肯定是需要存在的，所以通过评论id进行查询一下，当前这条评论是否存在
    3   判断当前用户的动作，是想进行点赞，还是想进行取消点赞
    4   需要查询当前这条评论，用户是否已经点赞，如果已经点赞，在点击就是取消，如果没有点赞，在点击就是进行点赞
    5   如果需要符合点赞的条件，那么必须要知道当前这条点赞的评论是谁进行的点赞，也就是查询user_id ,还必须满足当前评论必须存在，所以查询评论的id

    """
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    comment = Comment.query.get(comment_id)

    if action ==  "add":
        comment_like = CommentLike.query.filter(CommentLike.comment_id==comment.id,CommentLike.user_id==user.id).first()
        if not comment_like:
            comment_like = CommentLike()
            comment_like.user_id = user.id
            comment_like.comment_id = comment.id
            db.session.add(comment_like)

            comment.like_count += 1
    else:
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment.id,
                                                CommentLike.user_id == user.id).first()

        if comment_like:
            db.session.delete(comment_like)
            comment.like_count -= 1
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="ok")


@news_blue.route("/news_comment",methods=["POST"])
@user_login_data
def news_comment():
    """评论"""
    user = g.user
    news_id = request.json.get("news_id")
    comment_str = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    """
    新闻评论：
    １　:　如果需要对新闻进行评论，那么当前用户必须要先登陆
    2  :　如果需要对新闻进行评论，那么当前新闻肯定是需要存在的，所以直接通过新闻的id可以查询当前这条新闻
    3 　: 如果评论成功之后，那么我肯定希望下次在进来的时候，能够看到当前的评论，所以这个评论必须存到数据库里面
    """
    if not user :
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")


    news = News.query.get(news_id)

    comment  = Comment()
    comment.news_id = news_id
    comment.user_id = user.id
    comment.content = comment_str
    # 这个地方需要注意：不可能所有的评论都是有父id,所以需要判断
    if parent_id:
        comment.parent_id  = parent_id

    db.session.add(comment)
    db.session.commit()

    return jsonify(errno = RET.OK,errmsg = "评论成功",data = comment.to_dict())


@news_blue.route("/news_collect",methods=["POST"])
@user_login_data
def news_collect():
    """收藏"""
    user = g.user
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    """
    收藏新闻：
    １　:如果需要收藏新闻，那么必须新闻是存在的，所以先查询出来新闻
    2  : 新闻是人在收藏，所以用户是必须要登陆，才能收藏
    3  : 如果用户在，新闻也在，那么直接判断用户的动作，到底是收藏还是取消收藏
    """

    news = News.query.get(news_id)

    if not user :
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if action == "collect":
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)


    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="ok")











@news_blue.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    """新闻详情"""
    user = g.user
    news = News.query.get(news_id)
    # # 从session取用户登陆的数据，
    # # user.id表示唯一标识
    # user_id = session.get("user_id")
    # # 给用户一个默认值
    # user = None
    # # 如果有数据说明用户已经登陆，如果取出来的数据为none,说明用户没有登陆
    # if user_id:
    #     user = User.query.get(user_id)

    """右边的点击排行"""
    news_model = News.query.order_by(News.clicks.desc()).limit(10)
    news_clicks = []
    for news_dict in news_model:
        news_clicks.append(news_dict.to_dict())

    """
        进入到新闻详情页之后，如果用户已收藏该新闻，则显示已收藏，点击则为取消收藏，反之点击收藏该新闻
        1 : 通过一个变量进行控制当前的新闻是否已经收藏，默认情况下，所有的新闻第一次进来肯定是没有收藏，所以设置flase
        2 : 新闻已经收藏 is_collected = true ,
        3 :　因为我们做的收藏新闻，所以新闻至少是存在的，才能收藏，news 必须有新闻
        4 :　因为我们做的收藏新闻，新闻都是人在收藏，所以user必须有值，user必须登陆，
        """
    is_collected = False
    if user:
        if news in user.collection_news:
            is_collected = True


    """
    关注:
    1 第一次进来肯定没有关注任何人,所以默认值是false
    2 必须登陆,判断user是否有值
    3 必须有作者,因为如果是爬虫爬过来的数据,那么就没有新闻作者
    4 如果当前新闻有作者,并且在我关注的人的列表当中,就说明我是新闻作者的粉丝,所以设置ture
    """
    # 当前登陆的用户是否关注当前新闻的作者
    is_followed = False

    if user:
        if news.user in user.followed :
            is_followed = True

    """
    查询新闻评论
    1 :　查询新闻评论，所有的评论都是用户进行提交的，如果是用户提交的评论，那么直接通过查询评论表里面的新闻id就可以
    2 : 在查询新闻评论的时候，那么必须按照时间进行排序，把最新的评论放到最上面，所以需要用到order_by
    """
    comments = Comment.query.filter(Comment.news_id==news.id).order_by(Comment.create_time.desc()).all()

    comment_likes = []
    comment_like_ids = []
    """
   获取到评论点赞数据

   """
    if user:
        # 查询出来该用户所有的点赞
        comment_likes = CommentLike.query.filter(CommentLike.user_id == user.id).all()
        comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]

    comment_list = []
    # 对所有的评论进行迭代
    for comment in comments:
        comment_dict = comment.to_dict()
        # 评论默认情况下，都不会被点赞，所以默认值是false,如果已经被点赞，那么就设置true
        comment_dict["is_like"] = False
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_list.append(comment_dict)


    data ={
        "user_info": user.to_dict() if user else None,
        "click_news_list": news_clicks,
        "news":news.to_dict(),
        "is_collected": is_collected,
        "comments":comment_list,
        "is_followed":is_followed
    }

    return render_template("news/detail.html",data = data)



