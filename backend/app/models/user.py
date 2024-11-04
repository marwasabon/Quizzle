from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model): #fix
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)  # New field for email
    first_name = db.Column(db.String(150), nullable=False)  # New field for first name
    last_name = db.Column(db.String(150), nullable=False)  # New field for last name
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))  # Link to Role
    role = db.relationship('Role', backref=db.backref('users', lazy=True))
    
        # Additional profile fields
    quizzes_attempted = db.Column(db.Integer, default=0)  
    last_quiz_score = db.Column(db.Float, default=0.0)  
    last_quiz_date = db.Column(db.DateTime)
    date_joined = db.Column(db.DateTime, nullable=True, default=db.func.current_timestamp())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
