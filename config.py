import os

class Config:
    # change the string below to anything random & secret before production
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # during local dev use SQLite in the project folder
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or
        "sqlite:///" + os.path.join(os.path.dirname(__file__), "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
