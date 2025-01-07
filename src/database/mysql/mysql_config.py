# mysql_config.py
from flask_mysqldb import MySQL
import os

#Config of MySql Original
class MySqlConfig(object):
     MYSQL_HOST =  os.getenv('DB_HOST')
     MYSQL_USER = os.getenv('DB_USERNAME')
     MYSQL_PASSWORD = os.getenv('DB_PASSWORD')
     MYSQL_DB = os.getenv('DB_DATABASE')

# MYSQL_HOST = 'srv1311.hstgr.io'




# Init MySql
class Database:
    def __init__(self):
        self.mysql = None

    def init_app(self, app):
        app.config.from_object(MySqlConfig)
        self.mysql = MySQL(app)
        app.extensions['db'] = self.mysql
 