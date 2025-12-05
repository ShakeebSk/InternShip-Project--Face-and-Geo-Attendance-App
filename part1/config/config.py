import os

class Config:
    SECRET_KEY = "Your Secret Key"
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost/attendance_db"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Shakeeb%40MySql@localhost/attendance_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FACE_THRESHOLD = 0.6

