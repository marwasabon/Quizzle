from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from .models.role import Role


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=150)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=150)])
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
    """Admin form for editing a user. Leave the password blank to keep it."""

    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=150)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=150)])
    role = SelectField('Role', coerce=int)
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]


class CreateUserForm(UserForm):
    """Admin form for creating a user; a password is required."""

    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])


class ConfirmForm(FlaskForm):
    """Empty form that only carries a CSRF token, used for delete buttons."""

    submit = SubmitField('Delete')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Submit')
