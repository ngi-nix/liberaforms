"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, datetime
from dateutil.relativedelta import relativedelta
from liberaforms import db
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.mutable import MutableDict
#from sqlalchemy.orm.attributes import flag_modified
from liberaforms.utils.database import CRUD
from liberaforms.models.form import Form
from liberaforms.models.answer import Answer
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils import validators
from liberaforms.utils import utils

from pprint import pprint

class User(db.Model, CRUD):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.Date, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    preferences = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    blocked = db.Column(db.Boolean, default=False)
    admin = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    validatedEmail = db.Column(db.Boolean, default=False)
    token = db.Column(JSONB, nullable=True)
    consentTexts = db.Column(ARRAY(JSONB), nullable=True)
    authored_forms = db.relationship("Form", cascade = "all, delete, delete-orphan")

    def __init__(self, **kwargs):
        self.created = datetime.datetime.now().isoformat()
        self.username = kwargs["username"]
        self.email = kwargs["email"]
        self.password_hash = validators.hash_password(kwargs["password"])
        self.preferences = kwargs["preferences"]
        self.blocked = False
        self.admin = kwargs["admin"]
        self.validatedEmail = kwargs["validatedEmail"]
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

    @property
    def enabled(self):
        if not self.validatedEmail:
            return False
        if self.blocked:
            return False
        return True

    def get_forms(self, **kwargs):
        kwargs['editor_id']=self.id
        return Form.find_all(**kwargs)

    def authored_forms_total(self, **kwargs):
        kwargs["author_id"] = self.id
        return Form.find_all(**kwargs).count()

    @property
    def language(self):
        return self.preferences["language"]

    @property
    def new_entry_notification_default(self):
        return self.preferences["newEntryNotification"]

    def is_admin(self):
        return True if self.admin['isAdmin']==True else False

    def is_root_user(self):
        return True if self.email in os.environ['ROOT_USERS'] else False

    def verify_password(self, password):
        return validators.verify_password(password, self.password_hash)

    def delete_user(self):
        # Before delete, remove this user from other form.editors{}
        forms = Form.find_all(editor_id=self.id)
        for form in forms:
            del form.editors[str(self.id)]
            form.save()
        self.delete()   # cascade delete user.authored_forms

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

    def toggle_new_entry_notification_default(self):
        if self.preferences["newEntryNotification"]==True:
            self.preferences["newEntryNotification"]=False
        else:
            self.preferences["newEntryNotification"]=True
        self.save()
        return self.preferences["newEntryNotification"]

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
                 "newEntryNotification": True}

    @staticmethod
    def default_admin_settings():
        return {
            "isAdmin": False,
            "notifyNewUser": False,
            "notifyNewForm": False
        }

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

    def get_entries(self, **kwargs):
        kwargs['author_id']=str(self.id)
        return Answer.find_all(**kwargs)

    def get_statistics(self, year="2020"):
        today = datetime.date.today().strftime("%Y-%m")
        one_year_ago = datetime.date.today() - datetime.timedelta(days=354)
        year, month = one_year_ago.strftime("%Y-%m").split("-")
        month = int(month)
        year = int(year)
        result={    "labels":[], "entries":[], "forms":[],
                    "total_entries":[], "total_forms": []}
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
        total_entries=0
        total_forms=0
        entry_filter=[Answer.author_id == self.id]
        form_filter=[Form.author_id == self.id]
        for year_month in result['labels']:
            date_str = year_month.replace('-', ', ')
            start_date = datetime.datetime.strptime(date_str, '%Y, %m')
            stop_date = start_date + relativedelta(months=1)
            entries_filter = entry_filter + [Answer.created >= start_date]
            entries_filter = entry_filter + [Answer.created < stop_date]
            forms_filter = form_filter + [Form.created >= start_date]
            forms_filter = form_filter + [Form.created < stop_date]
            monthy_entries = Answer.query.filter(*entries_filter).count()
            monthy_forms = Form.query.filter(*forms_filter).count()
            total_entries= total_entries + monthy_entries
            total_forms= total_forms + monthy_forms
            result['entries'].append(monthy_entries)
            result['forms'].append(monthy_forms)
            result['total_entries'].append(total_entries)
            result['total_forms'].append(total_forms)
        return result

    def can_inspect_form(self, form):
        if str(self.id) in form.editors or self.is_admin():
            return True
        return False
