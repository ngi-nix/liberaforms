from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, PasswordField, BooleanField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask import g
from flask_babel import lazy_gettext as _

from GNGforms import app
from GNGforms.persistence import User, Installation
from GNGforms.utils import sanitizeUsername, pwd_policy


class NewUser(FlaskForm):
    username = StringField(_("Username"), validators=[DataRequired()])
    email = StringField(_("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_("Password"), validators=[DataRequired()])
    password2 = PasswordField(_("Password again"), validators=[DataRequired(), EqualTo('password')])

    def validate_username(self, username):
        if username.data != sanitizeUsername(username.data):
            raise ValidationError(_("Username is not valid"))
            return False
        if username.data in app.config['RESERVED_USERNAMES']:
            raise ValidationError(_("Please use a different username"))
            return False
        if User.find(username=username.data):
            raise ValidationError(_("Please use a different username"))

    def validate_email(self, email):
        if User.find(email=email.data):
            raise ValidationError(_("Please use a different email address"))
        elif email.data in app.config['ROOT_USERS'] and Installation.isUser(email.data):
            # a root_user email can only be used once across all sites.
            raise ValidationError(_("Please use a different email address"))
            
    def validate_password(self, password):
        if pwd_policy.test(password.data):
            raise ValidationError(_("Your password is weak"))
            
            
class Login(FlaskForm):
    username = StringField(_("Username"), validators=[DataRequired()])
    password = PasswordField(_("Password"), validators=[DataRequired()])
    
    def validate_username(self, username):
        if username.data != sanitizeUsername(username.data):
            return False

class GetEmail(FlaskForm):
    email = StringField(_("Email address"), validators=[DataRequired(), Email()])
    
    
class ChangeEmail(FlaskForm):
    email = StringField(_("New email address"), validators=[DataRequired(), Email()])
    
    def validate_email(self, email):
        if User.find(email=email.data):
            raise ValidationError(_("Please use a different email address"))
        elif email.data in app.config['ROOT_USERS'] and Installation.isUser(email.data):
            # a root_user email can only be used once across all sites.
            raise ValidationError(_("Please use a different email address"))


class ResetPassword(FlaskForm):
    password = PasswordField(_("Password"), validators=[DataRequired()])
    password2 = PasswordField(_("Password again"), validators=[DataRequired(), EqualTo('password')])

    def validate_password(self, password):
        if pwd_policy.test(password.data):
            raise ValidationError(_("Your password is weak"))


class smtpConfig(FlaskForm):
    host = StringField(_("Email server"), validators=[DataRequired()])
    port = IntegerField(_("Port"))
    encryption = SelectField(_("Encryption"), choices=[ ('None', 'None'),
                                                        ('SSL', 'SSL'),
                                                        ('STARTTLS', 'STARTTLS (maybe)')])
    user = StringField(_("User"))
    password = StringField(_("Password"))
    noreplyAddress = StringField(_("Sender address"), validators=[DataRequired(), Email()])


class NewInvite(FlaskForm):
    email = StringField(_("New user's email"), validators=[DataRequired(), Email()])
    message = TextAreaField(_("Include message"))
    admin = BooleanField(_("Make the new user an Admin"))
    hostname = StringField(_("hostname"), validators=[DataRequired()])
    
    def validate_email(self, email):
        if User.find(email=email.data):
            raise ValidationError(_("Please use a different email address"))
        elif email.data in app.config['ROOT_USERS'] and Installation.isUser(email.data):
            # a root_user email can only be used once across all sites.
            raise ValidationError(_("Please use a different email address"))
