"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, datetime, markdown
from dateutil.relativedelta import relativedelta
import unicodecsv as csv
from flask import g
from flask_babel import gettext
from urllib.parse import urlparse

from liberaforms import app, db
from sqlalchemy.dialects.postgresql import JSONB
from liberaforms.utils.database import CRUD
from liberaforms.models.form import Form
from liberaforms.models.answer import Answer
from liberaforms.models.user import User

from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils import sanitizers
from liberaforms.utils import utils

#from pprint import pprint as pp

class Site(db.Model, CRUD):
    __tablename__ = "site"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.Date, nullable=False)
    hostname = db.Column(db.String, nullable=False)
    port = db.Column(db.String, nullable=True)
    siteName = db.Column(db.String, nullable=False)
    defaultLanguage = db.Column(db.String, nullable=False)
    menuColor = db.Column(db.String, nullable=False)
    scheme = db.Column(db.String, nullable=True)
    blurb = db.Column(JSONB, nullable=False)
    invitationOnly = db.Column(db.Boolean)
    consentTexts = db.Column(JSONB, nullable=False)
    newUserConsentment = db.Column(JSONB, nullable=True)
    smtpConfig = db.Column(JSONB, nullable=False)

    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)

    @classmethod
    def create(cls, hostname, scheme):
        real_path = os.path.realpath(__file__)
        with open(f'{os.path.dirname(real_path)}/../default_blurb.md', 'r') as defaultBlurb:
            defaultMD=defaultBlurb.read()
        blurb = {
            'markdown': defaultMD,
            'html': markdown.markdown(defaultMD)
        }
        newSiteData={
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "hostname": hostname,
            "port": None,
            "scheme": scheme,
            "blurb": blurb,
            "invitationOnly": True,
            "siteName": "LiberaForms!",
            "defaultLanguage": app.config['DEFAULT_LANGUAGE'],
            "menuColor": "#b71c1c",
            "consentTexts": [   ConsentText.get_empty_consent(
                                                id=utils.gen_random_string(),
                                                name="terms"),
                                ConsentText.get_empty_consent(
                                                id=utils.gen_random_string(),
                                                name="DPL")
                            ],
            "newUserConsentment": [],
            "smtpConfig": {
                "host": f"smtp.{hostname}",
                "port": 25,
                "encryption": "",
                "user": "",
                "password": "",
                "noreplyAddress": f"no-reply@{hostname}"
            }
        }
        new_site=Site(**newSiteData)
        new_site.save()
        Installation.get() #create the Installation if it doesn't exist
        return new_site

    @classmethod
    def find(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()
        if not site:
            site=cls.create(hostname=kwargs['hostname'], scheme="http")
        return site

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    @property
    def host_url(self):
        url= "%s://%s" % (self.scheme, self.hostname)
        if self.port:
            url = "%s:%s" % (url, self.port)
        return url+'/'

    def favicon_url(self):
        path="%s%s_favicon.png" % (app.config['FAVICON_FOLDER'], self.hostname)
        if os.path.exists(path):
            return "/static/images/favicon/%s_favicon.png" % self.hostname
        else:
            return "/static/images/favicon/default-favicon.png"

    def delete_favicon(self):
        path="%s%s_favicon.png" % (app.config['FAVICON_FOLDER'], self.hostname)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def save_blurb(self, MDtext):
        self.blurb = {  'markdown': sanitizers.escape_markdown(MDtext),
                        'html': sanitizers.markdown2HTML(MDtext)}
        self.save()

    @property
    def terms_consent_id(self):
        return self.consentTexts[0]['id']

    @property
    def DPL_consent_id(self):
        return self.consentTexts[1]['id']

    @property
    def termsAndConditions(self):
        return self.consentTexts[0]

    @property
    def data_consent(self):
        return self.consentTexts[1]

    def get_consent_for_display(self, id, enabled_only=True):
        #print("id to find: "+id)
        #print("site.terms_consent_id: "+self.terms_consent_id)
        #print("site.DPL_consent_id: "+self.DPL_consent_id)
        if id == self.terms_consent_id:
            return self.get_terms_and_conditions_for_display(enabled_only=enabled_only)
        if id == self.DPL_consent_id:
            return self.get_data_consent_for_display(enabled_only=enabled_only)

        # this method should return before this.
        print("ERROR")
        return ConsentText.get_empty_consent()

        # need to test this
        consent = ConsentText._get_consent_by_id(id, self)
        if consent and (enabled_only and not consent['enabled']):
            return ConsentText.get_empty_consent(id=consent['id'])
        return ConsentText.get_consent_for_display(id, self)

    def get_terms_and_conditions_for_display(self, enabled_only=True):
        consent=self.termsAndConditions
        if (enabled_only and not consent['enabled']):
            consent = ConsentText.default_terms(id=self.terms_consent_id)
            consent['label'] = ""
            return consent
        if not consent['markdown']:
            consent = ConsentText.default_terms(id=consent['id'],
                                                enabled=consent['enabled'])
        consent['label'] = consent['label'] if consent['label'] else ""
        return consent

    def get_data_consent_for_display(self, enabled_only=True):
        consent=self.data_consent
        if (enabled_only and not consent['enabled']):
            consent = ConsentText.default_DPL(id=self.DPL_consent_id)
            consent['label'] = ""
            return consent
        if not consent['markdown']:
            consent = ConsentText.default_DPL(  id=consent['id'],
                                                enabled=consent['enabled'])
        consent['label'] = consent['label'] if consent['label'] else ""
        return consent

    def update_included_new_user_consentment_texts(self, id):
        if id in self.newUserConsentment:
            self.newUserConsentment.remove(id)
            self.save()
            return False
        else:
            if id == self.terms_consent_id:
                self.newUserConsentment.insert(0, id)
            elif id == self.DPL_consent_id:
                self.newUserConsentment.append(id)
            else:
                self.newUserConsentment.insert(-1, id)
            self.save()
            return True

    def toggle_consent_enabled(self, id):
        return ConsentText.toggle_enabled(id, self)

    def save_consent(self, id, data):
        consent = [item for item in self.consentTexts if item["id"]==id]
        consent = consent[0] if consent else None
        if not consent:
            return None
        consent['markdown'] = sanitizers.escape_markdown(data['markdown'].strip())
        consent['html'] = sanitizers.markdown2HTML(consent['markdown'])
        consent['label'] = sanitizers.strip_html_tags(data['label']).strip()
        consent['required'] = utils.str2bool(data['required'])
        if id == self.terms_consent_id:
            consent['required'] = True
            if not consent['markdown']:
                consent['markdown'] = ConsentText.default_terms()['markdown']
                consent['html'] = ConsentText.default_terms()['html']
        if id == self.DPL_consent_id:
            consent['required'] = True
            if not consent['markdown']:
                consent['markdown'] = ConsentText.default_DPL()['markdown']
                consent['html'] = ConsentText.default_DPL()['html']
        self.save()
        return consent

    def save_smtp_config(self, **kwargs):
        self.smtpConfig=kwargs
        self.save()

    def get_admins(self):
        return User.find_all(isAdmin=True)

    def toggle_invitation_only(self):
        self.invitationOnly = False if self.invitationOnly else True
        self.save()
        return self.invitationOnly

    def toggle_scheme(self):
        self.scheme = 'https' if self.scheme=='http' else 'http'
        self.save()
        return self.scheme

    def delete_site(self):
        users=User.find_all(hostname=self.hostname)
        for user in users:
            user.delete_user()
        invites = Invite.find_all(hostname=self.hostname)
        for invite in invites:
            invite.delete()
        return self.delete()

    def get_forms(self, **kwargs):
        return Form.find_all(**kwargs)

    def get_entries(self, **kwargs):
        return Answer.find_all(**kwargs)

    def get_users(self, **kwargs):
        return User.find_all(**kwargs)
    """
    def get_admins(self):
        return User.query.filter(User.admin.contains({"isAdmin": True}))
    """

    def get_statistics(self, **kwargs):
        today = datetime.date.today().strftime("%Y-%m")
        one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
        year, month = one_year_ago.strftime("%Y-%m").split("-")
        month = int(month)
        year = int(year)
        result={    "labels":[], "entries":[], "forms":[], 'users':[],
                    "total_entries":[], "total_forms": [], "total_users":[]}
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
        total_users=0
        for year_month in result['labels']:
            date_str = year_month.replace('-', ', ')
            start_date = datetime.datetime.strptime(date_str, '%Y, %m')
            stop_date = start_date + relativedelta(months=1)
            monthy_users = User.query.filter(
                                    User.created >= start_date,
                                    User.created < stop_date).count()
            monthy_forms = Form.query.filter(
                                    Form.created >= start_date,
                                    Form.created < stop_date).count()
            monthy_entries = Answer.query.filter(
                                    Answer.created >= start_date,
                                    Answer.created < stop_date).count()
            total_entries = total_entries + monthy_entries
            total_forms= total_forms + monthy_forms
            total_users = total_users + monthy_users
            result['entries'].append(monthy_entries)
            result['forms'].append(monthy_forms)
            result['users'].append(monthy_users)
            result['total_entries'].append(total_entries)
            result['total_forms'].append(total_forms)
            result['total_users'].append(total_users)
        return result

    def write_users_csv(self):
        fieldnames=["username", "created", "enabled", "email", "forms", "admin"]
        fieldheaders={  "username": gettext("Username"),
                        "created": gettext("Created"),
                        "enabled": gettext("Enabled"),
                        "email": gettext("Email"),
                        "forms": gettext("Forms"),
                        "admin": gettext("Admin")
                        }
        csv_name = os.path.join(app.config['TMP_DIR'], f"{self.hostname}.users.csv")
        with open(csv_name, mode='wb') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=fieldnames,
                                    extrasaction='ignore')
            writer.writerow(fieldheaders)
            for user in self.get_users():
                is_enabled = gettext("True") if user.enabled else gettext("False")
                is_admin = gettext("True") if user.is_admin() else gettext("False")
                row = { "username": user.username,
                        "created": user.created.strftime("%Y-%m-%d"),
                        "enabled": is_enabled,
                        "email": user.email,
                        "forms": user.get_forms().count(),
                        "admin": is_admin
                        }
                writer.writerow(row)
        return csv_name


class Installation(db.Model, CRUD):
    __tablename__ = "installation"
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    schemaVersion = db.Column(db.Integer, nullable=False)
    created = db.Column(db.Date, nullable=False)

    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)

    @classmethod
    def get(cls):
        installation=cls.query.first()
        if not installation:
            installation=Installation.create()
        return installation

    @classmethod
    def create(cls):
        if cls.objects.first():
            return
        data={  "name": "LiberaForms",
                "schemaVersion": app.config['SCHEMA_VERSION'],
                "created": datetime.date.today().strftime("%Y-%m-%d")}
        new_installation=cls(**data)
        new_installation.save()
        return new_installation

    def is_schema_up_to_date(self):
        return True if self.schemaVersion == app.config['SCHEMA_VERSION'] else False

    def update_schema(self):
        from liberaforms.utils.migrate import migrateMongoSchema
        if not self.is_schema_up_to_date():
            migrated_up_to=migrateMongoSchema(self.schemaVersion)
            self.schemaVersion=migrated_up_to
            self.save()
            return True if self.is_schema_up_to_date() else False
        else:
            True

    @staticmethod
    def get_sites(**kwargs):
        return Site.query.filter_by(**kwargs)

    @staticmethod
    def get_admins(**kwargs):
        return User.query.filter(User.admin.contains({"isAdmin": True}))

    @classmethod
    def write_admins_csv(cls):
        fieldnames=["hostname", "username", "created", "enabled", "email", "forms"]
        fieldheaders={  "username": gettext("Username"),
                        "created": gettext("Created"),
                        "enabled": gettext("Enabled"),
                        "email": gettext("Email"),
                        "forms": gettext("Forms")
                        }
        csv_name = os.path.join(app.config['TMP_DIR'], "LiberaForms.admin.csv")
        with open(csv_name, mode='wb') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=fieldnames,
                                    extrasaction='ignore')
            writer.writerow(fieldheaders)
            for user in cls.get_admins():
                row = { "username": user.username,
                        "created": user.created,
                        "enabled": gettext("True") if user.enabled else gettext("False"),
                        "email": user.email,
                        "forms": user.get_forms().count(),
                        "admin": gettext("True") if user.is_admin() else gettext("False"),
                        "hostname": user.hostname
                        }
                writer.writerow(row)
        return csv_name

    @staticmethod
    def is_user(email):
        return True if User.objects(email=email).first() else False
