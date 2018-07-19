
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from info import create_app,db
from info import  models
from info.models import User

app = create_app("development")
manager = Manager(app)

Migrate(app,db)
manager.add_command("db",MigrateCommand)



# -n:表示在使用脚本传输数据的时候，需要用到的值
@manager.option('-n', '--name', dest='name')
@manager.option('-p', '--password', dest='password')
def create_super_user(name,password):
    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True
    db.session.add(user)
    db.session.commit()




if __name__ == '__main__':
    print(app.url_map)
    manager.run()