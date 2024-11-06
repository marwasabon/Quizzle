from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, SelectField, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email,Length, EqualTo

from .models.role import Role

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=150)])  # New email field
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=150)])  # New first name field
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=150)])  # New last name field
    role = SelectField('Role', choices=[], coerce=int)  # Dropdown for roles
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
class ProfileForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=150)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=150)])
    submit = SubmitField('Update Profile')
    
class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('Role')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Save')
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.all()]  # Populate 
            
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Submit')
    