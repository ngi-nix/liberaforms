"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, shutil
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import pathlib
from liberaforms import db
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlalchemy.ext.mutable import MutableDict
from flask import current_app
from liberaforms.utils.database import CRUD
from liberaforms.models.form import Form
from liberaforms.models.formuser import FormUser
from liberaforms.models.answer import Answer, AnswerAttachment
from liberaforms.models.media import Media
from liberaforms.utils.storage.remote import RemoteStorage
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils import validators
from liberaforms.utils import crypto
from liberaforms.utils import utils

from pprint import pprint

class User(db.Model, CRUD):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(TIMESTAMP, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    preferences = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    blocked = db.Column(db.Boolean, default=False)
    admin = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    validatedEmail = db.Column(db.Boolean, default=False)
    uploads_enabled = db.Column(db.Boolean, default=False, nullable=False)
    uploads_limit = db.Column(db.Integer, nullable=False)
    token = db.Column(JSONB, nullable=True)
    consentTexts = db.Column(ARRAY(JSONB), nullable=True)
    authored_forms = db.relationship("Form", cascade = "all, delete, delete-orphan")
    timezone = db.Column(db.String, nullable=True)
    fedi_auth = db.Column(MutableDict.as_mutable(JSONB), nullable=True)
    media = db.relationship("Media",
                            lazy='dynamic',
                            cascade = "all, delete, delete-orphan")

    def __init__(self, **kwargs):
        self.created = datetime.now(timezone.utc)
        self.username = kwargs["username"]
        self.email = kwargs["email"]
        self.password_hash = validators.hash_password(kwargs["password"])
        self.preferences = kwargs["preferences"]
        self.blocked = False
        self.admin = kwargs["admin"]
        self.validatedEmail = kwargs["validatedEmail"]
        self.uploads_enabled = kwargs["uploads_enabled"]
        self.uploads_limit = utils.string_to_bytes(kwargs["uploads_limit"])
        self.token = {}
        self.consentTexts = []

    def __str__(self):
        return utils.print_obj_values(self)

    @property
    def site(self):
        from liberaforms.models.site import Site
        return Site.query.first()

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def find_all(cls, **kwargs):
        filters = []
        if 'token' in kwargs:
            filters.append(cls.token.contains({'token':kwargs['token']}))
            kwargs.pop('token')
        if 'isAdmin' in kwargs:
            filters.append(cls.admin.contains({"isAdmin":kwargs['isAdmin']}))
            kwargs.pop('isAdmin')
        if 'notifyNewForm' in kwargs:
            filters.append(cls.admin.contains({
                                "notifyNewForm": kwargs['notifyNewForm']
                            }))
            kwargs.pop('notifyNewForm')
        if 'notifyNewUser' in kwargs:
            filters.append(cls.admin.contains({
                                "notifyNewUser": kwargs['notifyNewUser']
                            }))
            kwargs.pop('notifyNewUser')
        for key, value in kwargs.items():
            filters.append(getattr(cls, key) == value)
        return cls.query.filter(*filters)

    def get_created_date(self):
        return utils.utc_to_g_timezone(self.created).strftime("%Y-%m-%d")
        #return self.created.astimezone(g.timezone).strftime("%Y-%m-%d")

    @property
    def enabled(self):
        if not self.validatedEmail:
            return False
        if self.blocked:
            return False
        return True

    def get_timezone(self):
        if self.timezone:
            return self.timezone
        return current_app.config['DEFAULT_TIMEZONE']

    def get_form(self, form_id, **kwargs):
        kwargs = {**{'form_id':form_id}, **kwargs}
        return self.get_forms(**kwargs).first()

    def get_forms(self, **kwargs):
        kwargs = {**{'user_id': self.id}, **kwargs}
        return Form.query.join(FormUser, Form.id == FormUser.form_id) \
                         .filter_by(**kwargs)

    def authored_forms_total(self, **kwargs):
        kwargs["author_id"] = self.id
        return Form.find_all(**kwargs).count()

    def can_inspect_form(self, form):
        if self.is_admin():
            return True
        if FormUser.find(user_id=self.id, form_id=form.id, is_editor=True):
            return True
        return False

    @property
    def language(self):
        return self.preferences["language"]

    def new_form_notifications(self):
        return {'newAnswer': self.preferences["newAnswerNotification"],
                'expiredForm': True}

    @property
    def new_answer_notification_default(self):
        return self.preferences["newAnswerNotification"]

    def is_admin(self):
        return True if self.admin['isAdmin']==True else False

    def is_root_user(self):
        return True if self.email in current_app.config['ROOT_USERS'] else False

    def verify_password(self, password):
        return validators.verify_password(password, self.password_hash)

    def get_media_dir(self):
        return os.path.join(current_app.config['UPLOADS_DIR'],
                            current_app.config['MEDIA_DIR'],
                            str(self.id))

    def media_usage(self):
        return Media.calc_total_size(user_id=self.id)

    def attachments_usage(self):
        return AnswerAttachment.calc_total_size(author_id=self.id)

    def total_uploads_usage(self):
        return self.media_usage() + self.attachments_usage()

    def can_enable_uploads(self):
        if not (current_app.config['ENABLE_UPLOADS'] and current_app.config['CRYPTO_KEY']):
            return False
        return True if self.total_uploads_usage() < self.uploads_limit else False

    def can_upload(self):
        if not self.can_enable_uploads():
            return False
        return self.uploads_enabled

    def toggle_uploads_enabled(self):
        if not self.can_enable_uploads():
            return False
        self.uploads_enabled = False if self.uploads_enabled else True
        self.save()
        return self.uploads_enabled

    def delete_user(self):
        # remove this user from FormUser
        for formuser in FormUser.find_all(user_id=self.id):
            if formuser.form.author_id != self.id:
                formuser.delete()
        # delete uploaded media files
        shutil.rmtree(self.get_media_dir(), ignore_errors=True)
        if current_app.config['ENABLE_REMOTE_STORAGE'] == True:
            prefix = "media/{}".format(self.id)
            RemoteStorage().remove_directory(prefix)
        # cascade delete user.authored_forms
        # cascade delete user.media
        self.delete()

    def set_token(self, **kwargs):
        self.token=utils.create_token(User, **kwargs)
        self.save()

    def delete_token(self):
        self.token={}
        self.save()

    def toggle_blocked(self):
        if self.is_root_user():
            self.blocked=False
        else:
            self.blocked=False if self.blocked else True
        self.save()
        return self.blocked

    def toggle_new_answer_notification_default(self):
        if self.preferences["newAnswerNotification"]==True:
            self.preferences["newAnswerNotification"]=False
        else:
            self.preferences["newAnswerNotification"]=True
        self.save()
        return self.preferences["newAnswerNotification"]

    def toggle_admin(self):
        if self.is_root_user():
            return self.is_admin()
        self.admin['isAdmin']=False if self.is_admin() else True
        self.save()
        return self.is_admin()

    @staticmethod
    def default_user_preferences(site=None):
        if site:
            default_language = site.defaultLanguage
        else:
            default_language = os.environ['DEFAULT_LANGUAGE']
        return { "language": default_language,
                 "newAnswerNotification": True,
                 "show_edit_alert": True}

    @staticmethod
    def default_admin_settings():
        return {
            "isAdmin": False,
            "notifyNewUser": False,
            "notifyNewForm": False,
            "forms": {},
            "users": {},
            "userforms": {}
        }

    def get_fedi_auth(self):
        if not self.fedi_auth:
            return {"node_url": "", "access_token": ""}
        else:
            return crypto.decrypt_dict(self.fedi_auth)

    def set_fedi_auth(self, auth_dict):
        self.fedi_auth = crypto.encrypt_dict(auth_dict)

    """
    send this admin an email when a new user registers at the site
    """
    def toggle_new_user_notification(self):
        if not self.is_admin():
            return False
        self.admin['notifyNewUser']=False if self.admin['notifyNewUser'] else True
        self.save()
        return self.admin['notifyNewUser']

    """
    send this admin an email when a new form is created
    """
    def toggle_new_form_notification(self):
        if not self.is_admin():
            return False
        self.admin['notifyNewForm']=False if self.admin['notifyNewForm'] else True
        self.save()
        return self.admin['notifyNewForm']

    def get_answers(self, **kwargs):
        kwargs['author_id']=str(self.id)
        return Answer.find_all(**kwargs)

    def get_statistics(self, year="2020"):
        today = datetime.now(timezone.utc).strftime("%Y-%m")
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=354)
        year, month = one_year_ago.strftime("%Y-%m").split("-")
        month = int(month)
        year = int(year)
        result={    "labels":[], "answers":[], "forms":[],
                    "total_answers":[], "total_forms": []}
        while 1:
            month = month +1
            if month == 13:
                month = 1
                year = year +1
            two_digit_month="{0:0=2d}".format(month)
            year_month = f"{year}-{two_digit_month}"
            result['labels'].append(year_month)
            if year_month == today:
                break
        total_answers=0
        total_forms=0
        answer_filter=[Answer.author_id == self.id]
        form_filter=[Form.author_id == self.id]
        for year_month in result['labels']:
            date_str = year_month.replace('-', ', ')
            start_date = datetime.strptime(date_str, '%Y, %m')
            stop_date = start_date + relativedelta(months=1)
            monthy_users = User.query.filter(
                                    User.id == self.id,
                                    User.created >= start_date,
                                    User.created < stop_date).count()
            monthy_forms = Form.query.filter(
                                    Form.author_id == self.id,
                                    Form.created >= start_date,
                                    Form.created < stop_date).count()
            monthy_answers = Answer.query.filter(
                                    Answer.author_id == self.id,
                                    Answer.created >= start_date,
                                    Answer.created < stop_date).count()
            total_answers = total_answers + monthy_answers
            total_forms= total_forms + monthy_forms
            result['answers'].append(monthy_answers)
            result['forms'].append(monthy_forms)
            result['total_answers'].append(total_answers)
            result['total_forms'].append(total_forms)
        return result
