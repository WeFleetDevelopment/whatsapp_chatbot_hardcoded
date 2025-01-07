# mysql_config.py
from flask_mysqldb import MySQL
import os

#Config of MySql Original
class MySqlConfig(object):
     MYSQL_HOST =  '193.203.175.68'
     MYSQL_USER = 'u823376988_fletzy_bd_test'
     MYSQL_PASSWORD = 'ajsid9ajd90aj82j9jsadjasjd82hjtdkjasSDS?'
     MYSQL_DB = 'u823376988_fletzy_test'

# MYSQL_HOST = 'srv1311.hstgr.io'  
 

  
 
# Init MySql
class Database:
    def __init__(self):
        self.mysql = None

    def init_app(self, app):
        app.config.from_object(MySqlConfig)
        self.mysql = MySQL(app)
        app.extensions['db'] = self.mysql
 