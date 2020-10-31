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

from flask import request, g
from flask_babel import gettext
from urllib.parse import urlparse
import os, datetime, markdown

from liberaforms import app, db
from liberaforms.models.form import Form, FormResponse
from liberaforms.models.user import User

from liberaforms.utils.queryset import HostnameQuerySet
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils import sanitizers
from liberaforms.utils import utils

#from pprint import pprint as pp

class Site(db.Document):
    meta = {'collection': 'sites', 'queryset_class': HostnameQuerySet}
    created = db.StringField(required=True)
    hostname = db.StringField(required=True)
    port = db.StringField(required=False)
    siteName = db.StringField(required=True)
    defaultLanguage=db.StringField(required=True)
    menuColor=db.StringField(required=True)
    scheme = db.StringField(required=False)
    blurb = db.DictField(required=True)
    invitationOnly = db.BooleanField()
    consentTexts = db.ListField(required=True)
    newUserConsentment = db.ListField(required=False)
    smtpConfig = db.DictField(required=True)

    def __init__(self, *args, **kwargs):        
        db.Document.__init__(self, *args, **kwargs)
    
    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)
    
    @classmethod
    def create(cls):
        hostname=urlparse(request.host_url).hostname
        with open('%s/../default_blurb.md' % os.path.dirname(os.path.realpath(__file__)), 'r') as defaultBlurb:
            defaultMD=defaultBlurb.read()
        blurb = {
            'markdown': defaultMD,
            'html': markdown.markdown(defaultMD)
        }
        newSiteData={
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "hostname": hostname,
            "port": None,
            "scheme": urlparse(request.host_url).scheme,
            "blurb": blurb,
            "invitationOnly": True,
            "siteName": "LiberaForms!",
            "defaultLanguage": app.config['DEFAULT_LANGUAGE'],
            "menuColor": "#b71c1c",
            "consentTexts": [   ConsentText.get_empty_consent(id=utils.gen_random_string(), name="terms"),
                                ConsentText.get_empty_consent(id=utils.gen_random_string(), name="DPL") ],
            "newUserConsentment": [],
            "smtpConfig": {
                "host": "smtp.%s" % hostname,
                "port": 25,
                "encryption": "",
                "user": "",
                "password": "",
                "noreplyAddress": "no-reply@%s" % hostname
            }
        }
        new_site=Site(**newSiteData)
        new_site.save()
        Installation.get() #create the Installation if it doesn't exist
        return new_site

    @classmethod
    def find(cls, *args, **kwargs):
        site = cls.find_all(*args, **kwargs).first()
        if not site:
            site=Site.create()
        return site

    @classmethod
    def find_all(cls, *args, **kwargs):
        return cls.objects.ensure_hostname(**kwargs)

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
            consent = ConsentText.default_terms(id=consent['id'], enabled=consent['enabled'])
        consent['label'] = consent['label'] if consent['label'] else ""
        return consent

    def get_data_consent_for_display(self, enabled_only=True):
        consent=self.data_consent
        if (enabled_only and not consent['enabled']):
            consent = ConsentText.default_DPL(id=self.DPL_consent_id)
            consent['label'] = ""
            return consent
        if not consent['markdown']:
            consent = ConsentText.default_DPL(id=consent['id'], enabled=consent['enabled'])
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
        return User.find_all(admin__isAdmin=True, hostname=self.hostname)
    
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

    """
    def get_chart_data(self, hostname=None):
        time_fields={"users": [], "forms": []}
        user_count=0
        users = User.find_all(hostname=hostname) if hostname else User.find_all()
        for user in users:
            user_count += 1
            time_fields["users"].append({"x": user.created, "y": user_count})
        form_count=0
        forms = Form.find_all(hostname=hostname) if hostname else Form.find_all()
        for form in forms:
            form_count += 1
            time_fields["forms"].append({"x": form.created, "y": form_count})
        return time_fields
    """
    
    def get_forms(self, **kwargs):
        kwargs['hostname'] = self.hostname
        return Form.find_all(**kwargs)

    def get_total_forms(self):
        return Form.find_all(hostname=self.hostname).count()

    def get_entries(self, **kwargs):
        kwargs['hostname'] = self.hostname
        return FormResponse.find_all(**kwargs)
        
    def get_total_users(self):
        return User.find_all(hostname=self.hostname).count()
    
    def get_statistics(self, **kwargs):
        today = datetime.date.today().strftime("%Y-%m")
        one_year_ago = datetime.date.today() - datetime.timedelta(days=354)
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
            year_month = "{}-{}".format(year, two_digit_month)
            result['labels'].append(year_month)
            if year_month == today:
                break
        total_entries=0
        total_forms=0
        total_users=0
        if not g.is_root_user_enabled and not 'hostname' in kwargs:
            kwargs['hostname'] = self.hostname
        for year_month in result['labels']:
            kwargs['created__startswith'] = year_month
            monthy_entries = FormResponse.find_all(**kwargs).count()
            monthy_forms = Form.find_all(**kwargs).count()
            monthy_users = User.find_all(**kwargs).count()
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


class Invite(db.Document):
    meta = {'collection': 'invites', 'queryset_class': HostnameQuerySet}
    hostname = db.StringField(required=True)
    email = db.EmailField(required=True)
    message = db.StringField(required=False)
    token = db.DictField(required=True)
    admin = db.BooleanField()
   
    def __init__(self, *args, **kwargs):        
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)

    @classmethod
    def create(cls, hostname, email, message, admin=False):
        data={
            "hostname": hostname,
            "email": email,
            "message": message,
            "token": utils.create_token(Invite),
            "admin": admin
        }
        newInvite=Invite(**data)
        newInvite.save()
        return newInvite

    @classmethod
    def find(cls, **kwargs):
        if 'token' in kwargs:
            kwargs={"token__token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.objects.ensure_hostname(**kwargs)
    
    def get_link(self):
        return "{}user/new/{}".format(  Site.find(hostname=self.hostname).host_url,
                                        self.token['token'])
    
    def get_message(self):
        return "{}\n\n{}".format(self.message, self.get_link())

    def set_token(self, **kwargs):
        self.invite['token']=utils.create_token(Invite, **kwargs)
        self.save()
        
    @staticmethod
    def default_message():
        return gettext("Hello,\n\nYou have been invited to LiberaForms.\n\nRegards.")
        

class Installation(db.Document):
    name = db.StringField(required=True)
    schemaVersion = db.IntField(required=True)
    created = db.StringField(required=True)
   
    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)

    @classmethod
    def get(cls):
        installation=cls.objects.first()
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
    
    @classmethod
    def get_sites(cls):
        return Site.objects()
    
    @staticmethod
    def is_user(email):
        return True if User.objects(email=email).first() else False
