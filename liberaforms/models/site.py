"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, markdown, shutil
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import unicodecsv as csv
from PIL import Image
from flask import current_app
from flask_babel import gettext as _

from liberaforms import db
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TIMESTAMP
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm.attributes import flag_modified
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
    created = db.Column(TIMESTAMP, nullable=False)
    hostname = db.Column(db.String, nullable=False)
    port = db.Column(db.Integer, nullable=True)
    scheme = db.Column(db.String, nullable=False, default="http")
    siteName = db.Column(db.String, nullable=False)
    defaultLanguage = db.Column(db.String, nullable=False)
    primary_color = db.Column(db.String, nullable=False)
    invitationOnly = db.Column(db.Boolean, default=True)
    consentTexts = db.Column(ARRAY(JSONB), nullable=False)
    newUserConsentment = db.Column(JSONB, nullable=True)
    smtpConfig = db.Column(JSONB, nullable=False)
    newuser_enableuploads = db.Column(db.Boolean, nullable=False, default=False)
    mimetypes = db.Column(JSONB, nullable=False)
    email_footer = db.Column(db.String, nullable=True)
    blurb = db.Column(JSONB, nullable=False)

    def __init__(self, hostname, port, scheme):
        self.created = datetime.now(timezone.utc)
        self.hostname = hostname
        self.port = port
        self.scheme = scheme
        self.siteName = "LiberaForms!"
        self.defaultLanguage = os.environ['DEFAULT_LANGUAGE']
        self.primary_color = "#D63D3B"
        self.consentTexts = [   ConsentText.get_empty_consent(
                                            id=utils.gen_random_string(),
                                            name="terms"),
                                ConsentText.get_empty_consent(
                                            id=utils.gen_random_string(),
                                            name="DPL")
                            ]
        self.newUserConsentment = []
        self.mimetypes = {
                "extensions": ["pdf", "png", "odt"],
                "mimetypes": ["application/pdf",
                              "image/png",
                              "application/vnd.oasis.opendocument.text"]
        }
        self.smtpConfig = {
                "host": f"smtp.{hostname}",
                "port": 25,
                "encryption": "",
                "user": "",
                "password": "",
                "noreplyAddress": f"no-reply@{hostname}"
        }
        blurb = os.path.join(current_app.root_path, '../assets/front-page.md')
        with open(blurb, 'r') as default_blurb:
            default_MD = default_blurb.read()
        self.blurb = {  'markdown': default_MD,
                        'html': markdown.markdown(default_MD)
                     }

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, url_parse=None):
        site = cls.query.first()
        if site:
            return site
        if url_parse:
            new_site = Site(
                hostname = url_parse.hostname,
                port = url_parse.port,
                scheme = url_parse.scheme
            )
            new_site.save()
            return new_site
        return None

    @property
    def host_url(self):
        url= f"{self.scheme}://{self.hostname}"
        if self.port:
            url = f"{url}:{self.port}"
        return url+'/'

    def change_email_header(self, file):
        """ Convert file to .png """
        new_header = Image.open(file)
        new_header.save(os.path.join(current_app.config['UPLOADS_DIR'],
                                     current_app.config['BRAND_DIR'],
                                     'emailheader.png'))

    def reset_email_header(self):
        email_header_path = os.path.join(current_app.config['UPLOADS_DIR'],
                                         current_app.config['BRAND_DIR'],
                                         'emailheader.png')
        default_email_header = os.path.join(current_app.config['UPLOADS_DIR'],
                                            current_app.config['BRAND_DIR'],
                                            'emailheader-default.png')
        shutil.copyfile(default_email_header, email_header_path)
        return True

    def change_favicon(self, file):
        """ Convert file to .ico and make the it square """
        img = Image.open(file)
        x, y = img.size
        size = max(32, x, y)
        #icon_sizes = [(16,16), (32, 32), (48, 48), (64,64)]
        new_favicon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        new_favicon.paste(img, (int((size - x) / 2), int((size - y) / 2)))
        new_favicon.save(os.path.join(current_app.config['UPLOADS_DIR'],
                                      current_app.config['BRAND_DIR'],
                                      'favicon.ico'))

    def reset_favicon(self):
        favicon_path = os.path.join(current_app.config['UPLOADS_DIR'],
                                    current_app.config['BRAND_DIR'],
                                    'favicon.ico')
        default_favicon = os.path.join(current_app.config['UPLOADS_DIR'],
                                       current_app.config['BRAND_DIR'],
                                       'favicon-default.ico')
        shutil.copyfile(default_favicon, favicon_path)
        return True

    def get_email_footer(self):
        return self.email_footer if self.email_footer else _("Ethical form software")

    def get_email_header_url(self):
        return f"{self.host_url}brand/emailheader.png"

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
            flag_modified(self, "newUserConsentment")
            self.save()
            return False
        else:
            if id == self.terms_consent_id:
                self.newUserConsentment.insert(0, id)
            elif id == self.DPL_consent_id:
                self.newUserConsentment.append(id)
            else:
                self.newUserConsentment.insert(-1, id)
            flag_modified(self, "newUserConsentment")
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
        flag_modified(self, "consentTexts")
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

    def toggle_newuser_uploads_default(self):
        self.newuser_enableuploads = False if self.newuser_enableuploads else True
        self.save()
        return self.newuser_enableuploads

    def toggle_scheme(self):
        self.scheme = 'https' if self.scheme=='http' else 'http'
        self.save()
        return self.scheme

    def get_forms(self, **kwargs):
        return Form.find_all(**kwargs)

    def get_answers(self, **kwargs):
        return Answer.find_all(**kwargs)

    def get_users(self, **kwargs):
        return User.find_all(**kwargs)

    def get_statistics(self, **kwargs):
        today = datetime.now(timezone.utc)
        one_year_ago = today - timedelta(days=365)
        year, month = one_year_ago.strftime("%Y-%m").split("-")
        month = int(month)
        year = int(year)
        result={    "labels":[], "answers":[], "forms":[], 'users':[],
                    "total_answers":[], "total_forms": [], "total_users":[]}
        while 1:
            month = month +1
            if month == 13:
                month = 1
                year = year +1
            two_digit_month="{0:0=2d}".format(month)
            year_month = f"{year}-{two_digit_month}"
            result['labels'].append(year_month)
            if year_month == today.strftime("%Y-%m"):
                break
        total_answers=0
        total_forms=0
        total_users=0
        for year_month in result['labels']:
            date_str = year_month.replace('-', ', ')
            start_date = datetime.strptime(date_str, '%Y, %m')
            stop_date = start_date + relativedelta(months=1)
            monthy_users = User.query.filter(
                                    User.created >= start_date,
                                    User.created < stop_date).count()
            monthy_forms = Form.query.filter(
                                    Form.created >= start_date,
                                    Form.created < stop_date).count()
            monthy_answers = Answer.query.filter(
                                    Answer.created >= start_date,
                                    Answer.created < stop_date).count()
            total_answers = total_answers + monthy_answers
            total_forms= total_forms + monthy_forms
            total_users = total_users + monthy_users
            result['answers'].append(monthy_answers)
            result['forms'].append(monthy_forms)
            result['users'].append(monthy_users)
            result['total_answers'].append(total_answers)
            result['total_forms'].append(total_forms)
            result['total_users'].append(total_users)
        return result

    def write_users_csv(self):
        fieldnames=["username", "created", "enabled", "email", "forms", "admin"]
        fieldheaders={  "username": _("Username"),
                        "created": _("Created"),
                        # i18n: Used as column title
                        "enabled": _("Enabled"),
                        # i18n: Email address, used as column title
                        "email": _("Email"),
                        # i18n: Used as column title
                        "forms": _("Forms"),
                        # i18n: Whether user is admin
                        "admin": _("Admin")
                        }
        csv_name = os.path.join(os.environ['TMP_DIR'], f"{self.hostname}.users.csv")
        with open(csv_name, mode='wb') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=fieldnames,
                                    extrasaction='ignore')
            writer.writerow(fieldheaders)
            for user in self.get_users():
                # i18n: Boolean option: True or False
                is_enabled = _("True") if user.enabled else _("False")
                is_admin = _("True") if user.is_admin() else _("False")
                row = { "username": user.username,
                        "created": user.created.strftime("%Y-%m-%d"),
                        "enabled": is_enabled,
                        "email": user.email,
                        "forms": user.get_forms().count(),
                        "admin": is_admin
                        }
                writer.writerow(row)
        return csv_name
