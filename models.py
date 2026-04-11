from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))  # hashed
    role = db.Column(db.String(10))  # D or E or ADMIN


class Routine(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nume = db.Column(db.String(100))
    club = db.Column(db.String(100))
    aparat = db.Column(db.String(50))

    D = db.Column(db.Float)

    E1 = db.Column(db.Float)
    E2 = db.Column(db.Float)
    E3 = db.Column(db.Float)
    E4 = db.Column(db.Float)
    E5 = db.Column(db.Float)

    penalty = db.Column(db.Float)

    final = db.Column(db.Float)

    status = db.Column(db.String(20))  # PENDING / APPROVED