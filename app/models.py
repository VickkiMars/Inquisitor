# flask_app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from . import db  # or from your app import db depending on structure
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import JSON
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

class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True, default=lambda: datetime.utcnow().date() + timedelta(days=30))
    duration_hour = db.Column(db.Integer, default=1)
    duration_minute = db.Column(db.Integer, default=0)
    instructions = db.Column(db.Text, nullable=True)
    assessment_questions = db.Column(JSON, nullable=True)
    def __repr__(self):
        return f"<Assessment {self.name} ({self.code})>"
    
class AssessmentResult(db.Model):
    __tablename__ = "assessment_results"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    reg_no = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)

    assessment = db.relationship('Assessment', backref=db.backref('results', lazy=True))

    def __repr__(self):
        return f"<AssessmentResult {self.student_name} - {self.score}>"
