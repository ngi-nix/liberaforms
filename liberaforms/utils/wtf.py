"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, PasswordField, BooleanField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask import g
from flask_babel import lazy_gettext as _

from liberaforms import app
from liberaforms.models import User, Installation
from liberaforms.utils.utils import sanitizeUsername, pwd_policy
import re


class NewUser(FlaskForm):
    username = StringField(_("Username"), validators=[DataRequired()])
    email = StringField(_("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_("Password"), validators=[DataRequired()])
    password2 = PasswordField(_("Password again"), validators=[DataRequired(), EqualTo('password')])
    termsAndConditions = BooleanField()
    DPLConsent = BooleanField()
    
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
            
    def validate_termsAndConditions(self, termsAndConditions):
        if g.site.TermsConsentID in g.site.newUserConsentment and not termsAndConditions.data:
            raise ValidationError(_("Please accept our terms and conditions"))

    def validate_DPLConsent(self, DPLConsent):
        if g.site.DPLConsentID in g.site.newUserConsentment and not DPLConsent.data:
            raise ValidationError(_("Please accept our data protection policy"))

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
    message = TextAreaField(_("Include message"), validators=[DataRequired()])
    admin = BooleanField(_("Make the new user an Admin"))
    hostname = StringField(_("hostname"), validators=[DataRequired()])
    
    def validate_email(self, email):
        if User.find(email=email.data, hostname=self.hostname.data):
            raise ValidationError(_("Please use a different email address"))
        elif email.data in app.config['ROOT_USERS'] and Installation.isUser(email.data):
            # a root_user email can only be used once across all sites.
            raise ValidationError(_("Please use a different email address"))


class ChangeMenuColor(FlaskForm):
    hex_color = StringField(_("HTML color code"), validators=[DataRequired()])
    def validate_hex_color(self, hex_color):
        if not bool(re.search("^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", hex_color.data)):
            raise ValidationError(_("Not a valid HTML color code"))
