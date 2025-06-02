from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id        = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email     = db.Column(db.String(120), unique=True, index=True, nullable=False)
    pw_hash   = db.Column(db.String(256), nullable=False)
    joined_on = db.Column(db.Date, default=date.today)

    # helpers
    def set_password(self, plain):
        self.pw_hash = generate_password_hash(plain)

    def check_password(self, plain) -> bool:
        return check_password_hash(self.pw_hash, plain)
