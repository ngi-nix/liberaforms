"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import datetime
from dateutil.relativedelta import relativedelta
from liberaforms import app, db
from sqlalchemy.dialects.postgresql import JSONB
from liberaforms.utils.crud import CRUD
from liberaforms.models.form import Form, FormResponse
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils import validators
from liberaforms.utils.utils import create_token

#from pprint import pprint as pp

class User(db.Model, CRUD):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.Date, nullable=False)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    hostname = db.Column(db.String, nullable=False)
    preferences = db.Column(JSONB, nullable=True)
    blocked = db.Column(db.Boolean)
    admin = db.Column(JSONB, nullable=False)
    validatedEmail = db.Column(db.Boolean)
    token = db.Column(JSONB, nullable=True)
    consentTexts = db.Column(JSONB, nullable=True)

    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)
        #print("User.__init__ {}".format(self.username))

    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)

    @property
    def site(self):
        #print("user.site")
        from liberaforms.models.site import Site
        return Site.find(hostname=self.hostname)

    @classmethod
    def create(cls, newUserData):
        newUser=User(**newUserData)
        newUser.save()
        return newUser

    @classmethod
    def find(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def find_all(cls, *args, **kwargs):
        if 'token' in kwargs:
            kwargs={"token__token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        return cls.query.filter_by(**kwargs)

    @property
    def enabled(self):
        if not self.validatedEmail:
            return False
        if self.blocked:
            return False
        return True

    def get_forms(self, **kwargs):
        kwargs['editor_id']=str(self.id)
        return Form.find_all(**kwargs)

    def get_authored_forms(self, **kwargs):
        kwargs['author_id']=str(self.id)
        return Form.find_all(**kwargs)

    @property
    def language(self):
        return self.preferences["language"]

    @property
    def new_entry_notification_default(self):
        return self.preferences["newEntryNotification"]

    def is_admin(self):
        return True if self.admin['isAdmin']==True else False

    def is_root_user(self):
        return True if self.email in app.config['ROOT_USERS'] else False

    def verify_password(self, password):
        return validators.verify_password(password, self.password_hash)

    def delete_user(self):
        forms = Form.find_all(author_id=str(self.id))
        for form in forms:
            form.delete_form()
        forms = Form.find_all(editor_id=str(self.id))
        for form in forms:
            del form.editors[str(self.id)]
            form.save()
        self.delete()

    def set_token(self, **kwargs):
        self.token=create_token(User, **kwargs)
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
        return FormResponse.find_all(**kwargs)

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
        entry_filter=[FormResponse.author_id == self.id]
        form_filter=[Form.author_id == self.id]
        for year_month in result['labels']:
            date_str = year_month.replace('-', ', ')
            start_date = datetime.datetime.strptime(date_str, '%Y, %m')
            stop_date = start_date + relativedelta(months=1)
            entries_filter = entry_filter + [FormResponse.created >= start_date]
            entries_filter = entry_filter + [FormResponse.created < stop_date]
            forms_filter = form_filter + [Form.created >= start_date]
            forms_filter = form_filter + [Form.created < stop_date]
            monthy_entries = FormResponse.query.filter(*entries_filter).count()
            monthy_forms = Form.query.filter(*forms_filter).count()
            total_entries= total_entries + monthy_entries
            total_forms= total_forms + monthy_forms
            result['entries'].append(monthy_entries)
            result['forms'].append(monthy_forms)
            result['total_entries'].append(total_entries)
            result['total_forms'].append(total_forms)
        return result

    def can_inspect_form(self, form):
        return True if (str(self.id) in form.editors or self.is_admin()) else False
