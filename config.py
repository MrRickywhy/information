import redis

class Config(object):


    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    SECRET_KEY = "sheybabdjsbavs"
    SESSION_TYPE = "redis"
    SESSION_USE_SINGER = True
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    PERMANENT_SESSION_LIFETIME = 86400



class DevelopementConfig(Config):
    DEBUG = True




class ProductionConfig(Config):

    pass



config = {
    "development": DevelopementConfig,
    "production": ProductionConfig
}