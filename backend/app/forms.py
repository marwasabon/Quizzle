from flask_wtf import FlaskForm
from wtforms import EmailField, SelectField, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email,Length, EqualTo

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
    submit = SubmitField('Login')
    
class ProfileForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=150)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=150)])
    submit = SubmitField('Update Profile')
