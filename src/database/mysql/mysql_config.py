from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

class Config:
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_DATABASE")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 300
    SQLALCHEMY_POOL_RECYCLE = 1800