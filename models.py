from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"

    ROLE_USER = 1
    ROLE_ADMIN = 2

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Integer, default=ROLE_USER)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_user(self):
        return self.role == self.ROLE_USER

    @property
    def password(self):
        raise AttributeError("Password is not readable")

    @password.setter
    def password(self, value):
        self.password_hash = generate_password_hash(value)


class Test(db.Model):
    __tablename__ = "tests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    author = db.relationship("User", backref="tests")


class Question(db.Model):
    __tablename__ = "questions"

    TYPE_SINGLE = "single"
    TYPE_MULTIPLE = "multiple"
    TYPE_TEXT = "text"
    TYPE_SCALE = "scale"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    options = db.Column(db.Text)

    test = db.relationship("Test", backref="questions")

    def is_choice_question(self):
        return self.question_type in {self.TYPE_SINGLE, self.TYPE_MULTIPLE}

    def is_text_question(self):
        return self.question_type == self.TYPE_TEXT

    def is_scale_question(self):
        return self.question_type == self.TYPE_SCALE


class UserResult(db.Model):
    __tablename__ = "user_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False)
    score = db.Column(db.Float)
    answers_json = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="results")
    test = db.relationship("Test", backref="results")
