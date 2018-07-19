


# 根据当前传过来的索引,判断返回具体的值
from flask import session,g

from info.models import User
import functools

def do_index_class(index):

    if index == 0:
        return "first"

    elif index == 1:
        return "second"

    elif index == 2:
        return "third"


    else:
        return ""




# def user_login_data():
#     # 从session取用户登陆的数据，
#     # user.id表示唯一标识
#     user_id = session.get("user_id")
#     # 给用户一个默认值
#     user = None
#     # 如果有数据说明用户已经登陆，如果取出来的数据为none,说明用户没有登陆
#     if user_id:
#         user = User.query.get(user_id)
#
#     return user



def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        # 从session取用户登陆的数据，
        # user.id表示唯一标识
        user_id = session.get("user_id")
        # 给用户一个默认值
        user = None
        # 如果有数据说明用户已经登陆，如果取出来的数据为none,说明用户没有登陆
        if user_id:
            user = User.query.get(user_id)
        g.user = user
        return f(*args,**kwargs)
    return wrapper