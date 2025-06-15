# flask_app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from . import db  # or from your app import db depending on structure
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'  # optional, defaults to 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed passwords

    def __repr__(self):
        return f"<User {self.username}>"

class QuestionHistory(db.Model):
    __tablename__ = 'question_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.Text, nullable=False)         # the user query or input
    questions = db.Column(db.Text, nullable=False)      # store as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    filename = db.Column(db.String(256), nullable=True)
    user = db.relationship('User', backref='history')

    def __repr__(self):
        return f"<History User:{self.user_id} at {self.created_at}>"
