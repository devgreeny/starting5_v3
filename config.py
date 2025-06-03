import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "mysql+mysqlconnector://devgreeny:ziknip-kAvni2-duhvek@devgreeny.mysql.pythonanywhere-services.com/devgreeny$default"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
