"""
“Copyright 2019 La Coordinadora d’Entitats per la Lleialtat Santsenca”

This file is part of GNGforms.

GNGforms is free software: you can redistribute it and/or modify
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

from GNGforms import app, db
from GNGforms.utils import *
from GNGforms.migrate import migrateMongoSchema
from flask import flash, request, g
from flask_babel import gettext 
from urllib.parse import urlparse
import os, string, random, datetime, json, markdown
from mongoengine import QuerySet
from pprint import pformat

#from pprint import pprint as pp


def get_obj_values_as_dict(obj):
    values = {}
    fields = type(obj).__dict__['_fields']
    for key, _ in fields.items():
        value = getattr(obj, key, None)
        values[key] = value
    return values

class HostnameQuerySet(QuerySet):
    def ensure_hostname(self, **kwargs):
        if not g.isRootUser and not 'hostname' in kwargs:
            kwargs={'hostname':g.site.hostname, **kwargs}
        #print("ensure_hostname kwargs: %s" % kwargs)
        return self.filter(**kwargs)


class User(db.Document):
    meta = {'collection': 'users', 'queryset_class': HostnameQuerySet}
    username = db.StringField(required=True)
    email = db.StringField(required=True)
    password =db.StringField(required=True)
    language = db.StringField(required=True)
    hostname = db.StringField(required=True)
    blocked = db.BooleanField()
    admin = db.DictField(required=True)
    validatedEmail = db.BooleanField()
    created = db.StringField(required=True)
    token = db.DictField(required=False)
    
    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        return pformat({'User': get_obj_values_as_dict(self)})
    
    @classmethod
    def create(cls, newUserData):
        newUser=User(**newUserData)
        newUser.save()
        return newUser

    @classmethod
    def find(cls, **kwargs):
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, *args, **kwargs):
        if 'token' in kwargs:
            kwargs={"token__token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        return cls.objects.ensure_hostname(**kwargs)

    @classmethod
    def getNotifyNewFormEmails(cls):
        emails=[]
        criteria={  'blocked':False,
                    'validatedEmail':True,
                    'admin__isAdmin':True,
                    'admin__notifyNewForm':True}
        admins=User.findAll(**criteria)
        for admin in admins:
            emails.append(admin['email'])
        rootUsers=User.objects(__raw__={'email': {"$in": app.config['ROOT_USERS']},
                                        'admin.notifyNewForm':True})
        for rootUser in rootUsers:
            if not rootUser['email'] in emails:
                emails.append(rootUser['email'])
        #print("new form notify %s" % emails)
        return emails

    @classmethod
    def getNotifyNewUserEmails(cls):
        emails=[]
        criteria={  'blocked':False,
                    'validatedEmail': True,
                    'admin__isAdmin':True,
                    'admin__notifyNewUser':True}
        admins=User.findAll(**criteria)
        for admin in admins:
            emails.append(admin['email'])
        rootUsers=User.objects(__raw__={'email':{"$in": app.config['ROOT_USERS']},
                                        'admin.notifyNewUser':True})
        for rootUser in rootUsers:
            if not rootUser['email'] in emails:
                emails.append(rootUser['email'])
        #print("new user notify: %s" % emails)
        return emails
    
    @property
    def enabled(self):
        if not self.validatedEmail:
            return False
        if self.blocked:
            return False
        return True
               
    @property
    def forms(self):
        return Form.findAll(editor=str(self.id))

    def isAdmin(self):
        return True if self.admin['isAdmin']==True else False

    def isRootUser(self):
        return True if self.email in app.config['ROOT_USERS'] else False
    
    def deleteUser(self):
        forms = Form.findAll(author_id=str(self.id))
        for form in forms:
            form.delete()
        forms = Form.findAll(editor=str(self.id))
        for form in forms:
            del form.editors[str(self.id)]
            form.save()
        self.delete()
    
    def setToken(self, **kwargs):
        self.token=createToken(User, **kwargs)
        self.save()

    def deleteToken(self):
        self.token={}
        self.save()

    def toggleBlocked(self):
        if self.isRootUser():
            self.blocked=False
        self.blocked=False if self.blocked else True
        self.save()
        return self.blocked
            
    def toggleAdmin(self):
        if self.isRootUser():
            return self.isAdmin()
        self.admin['isAdmin']=False if self.isAdmin() else True
        self.save()
        return self.isAdmin()

    @staticmethod
    def defaultAdminSettings():
        return {
            "isAdmin": False,
            "notifyNewUser": False,
            "notifyNewForm": False
        }

    """
    send this admin an email when a new user registers at the site
    """
    def toggleNewUserNotification(self):
        if not self.isAdmin():
            return False
        self.admin['notifyNewUser']=False if self.admin['notifyNewUser'] else True
        self.save()
        return self.admin['notifyNewUser']

    """
    send this admin an email when a new form is created
    """
    def toggleNewFormNotification(self):
        if not self.isAdmin():
            return False
        self.admin['notifyNewForm']=False if self.admin['notifyNewForm'] else True
        self.save()
        return self.admin['notifyNewForm']    

    def canInspectForm(self, form):
        return True if (str(self.id) in form.editors or self.isAdmin()) else False
    

class Form(db.Document):
    meta = {'collection': 'forms', 'queryset_class': HostnameQuerySet}
    created = db.StringField(required=True)
    hostname = db.StringField(required=True)
    slug = db.StringField(required=True)
    author_id = db.StringField(db_field="author", required=True)
    editors = db.DictField(required=True)
    postalCode = db.StringField(required=False)
    enabled = db.BooleanField()
    expired = db.BooleanField()
    expiryConditions = db.DictField(required=True)
    structure = db.StringField(required=True)
    fieldIndex = db.ListField(required=True)
    entries = db.ListField(required=False)
    sharedEntries = db.DictField(required=False)
    log = db.ListField(required=False)
    requireDataConsent = db.BooleanField()
    restrictedAccess = db.BooleanField()
    adminPreferences = db.DictField(required=True)
    afterSubmitText = db.DictField(required=True)
    site = None

    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)
        self.site=Site.objects(hostname=self.hostname).first()
   
    def __str__(self):
        return pformat({'Form': get_obj_values_as_dict(self)})
        
    @classmethod
    def find(cls, **kwargs):
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, **kwargs):
        if 'editor' in kwargs:
            kwargs={"__raw__": {'editors.%s' % kwargs["editor"]: {'$exists': True}}, **kwargs}
            kwargs.pop('editor')
        if 'key' in kwargs:
            kwargs={"sharedEntries__key": kwargs['key'], **kwargs}
            kwargs.pop('key')
        return cls.objects.ensure_hostname(**kwargs)

    @property
    def user(self):
        return self.author
        
    @property
    def author(self):
        return User.find(id=self.author_id)

    def changeAuthor(self, new_author):
        if new_author.enabled:
            if self.author_id in self.editors:
                del self.editors[self.author_id]
            self.author_id=str(new_author.id)
            if self.addEditor(new_author):
                self.save()
                return True
        return False

    def getFieldIndexForDataDisplay(self):
        """
        formbuilder adds HTML tags to labels like '<br>' or '<div></div>'.
        The tags (formatted lables) are good when rendering the form but we do not want them included in CSV column headers.
        This function is called when viewing form entry data.
        """
        result=[]
        for field in self.fieldIndex:
            result.append({'label': stripHTMLTagsForLabel(field['label']), 'name': field['name']})
        """ insert this optional field """
        if self.isDataConsentEnabled():
            result.insert(1, {"name": "DPL", "label": gettext("DPL")})
        return result
    
    @property
    def totalEntries(self):
        return len(self.entries)

    def isEnabled(self):
        if not (self.author.enabled and self.adminPreferences['public']):
            return False
        return self.enabled

    @classmethod
    def newEditorPreferences(cls):
        return {'notification': {'newEntry': False, 'expiredForm': True}}

    def addEditor(self, editor):
        if not editor.enabled:
            return False
        editor_id=str(editor.id)
        if not editor_id in self.editors:
            self.editors[editor_id]=Form.newEditorPreferences()
            self.save()
            return True
        return False

    def removeEditor(self, editor_id):
        if editor_id == self.author_id:
            return None
        if editor_id in self.editors:
            del self.editors[editor_id]
            self.save()
            return editor_id
        return None
   
    @property
    def url(self):
        return "%s%s" % (self.site.host_url, self.slug)  

    def isDataConsentEnabled(self):
        if not self.site.isPersonalDataConsentEnabled():
            return False
        else:
            return self.requireDataConsent

    @property
    def dataConsent(self):
        return self.site.personalDataConsent['html']

    @property
    def lastEntryDate(self):
        if self.entries:
            last_entry = self.entries[-1] 
            return last_entry["created"]
        else:
            return ""

    def getAvailableNumberTypeFields(self):
        result={}
        for element in json.loads(self.structure):
            if "type" in element and element["type"] == "number":
                if element["name"] in self.fieldConditions:
                    result[element["name"]]=self.fieldConditions[element["name"]]
                else:
                    result[element["name"]]={"type":"number", "condition": None}
        return result
        
    def getFieldLabel(self, fieldName):
        for element in json.loads(self.structure):
            if 'name' in element and element['name']==fieldName:
                return element['label']
        return None

    @property
    def fieldConditions(self):
        return self.expiryConditions["fields"]

    def getConditionalFieldPositions(self):
        conditionalFieldPositions=[]
        for fieldName, condition in self.fieldConditions.items():
            if condition['type'] == 'number':
                for position, field in enumerate(self.fieldIndex):
                    if field['name'] == fieldName:
                        conditionalFieldPositions.append(position)
                        break
        return conditionalFieldPositions

    @classmethod
    def saveNewForm(cls, formData):
        if formData['slug'] in app.config['RESERVED_SLUGS']:
            return None
        new_form=Form(**formData)
        new_form.save()
        return new_form

    def deleteEntries(self):
        self.entries=[]
        self.save()
    
    def isAuthor(self, user):
        return True if self.author_id == user.id else False
        
    def isEditor(self, user):
        return True if str(user.id) in self.editors else False

    def getEditors(self):
        editors=[]
        for editor_id in self.editors:
            #print (editor_id)
            user=User.find(id=editor_id)
            if user:
                editors.append(user)
            else:
                # remove editor_id from self.editors
                pass
        return editors

    def willExpire(self):
        if self.expiryConditions["expireDate"]:
            return True
        if self.expiryConditions["fields"]:
            return True
        return False
    
    def hasExpired(self):
        if not self.willExpire():
            return False
        if self.expiryConditions["expireDate"] and not isFutureDate(self.expiryConditions["expireDate"]):
            return True
        for fieldName, value in self.fieldConditions.items():
            if value['type'] == 'number':
                total=self.tallyNumberField(fieldName)
                if total >= int(value['condition']):
                    return True
        return False

    def tallyNumberField(self, fieldName):
        total=0
        for entry in self.entries:
            try:
                total = total + int(entry[fieldName])
            except:
                continue
        return total
                
    def isPublic(self):
        if not self.isEnabled() or self.expired:
            return False
        else:
            return True

    def isShared(self):
        if self.areEntriesShared():
            return True
        if len(self.editors) > 1:
            return True
        return False
    
    def areEntriesShared(self):
        return self.sharedEntries['enabled']
    
    def getSharedEntriesURL(self, part="results"):
        return "%s/%s/%s" % (self.url, part, self.sharedEntries['key'])

    def toggleEnabled(self):
        if self.expired or self.adminPreferences['public']==False:
            return False
        else:
            self.enabled = False if self.enabled else True
            self.save()
            return self.enabled
            
    def toggleAdminFormPublic(self):
        self.adminPreferences['public'] = False if self.adminPreferences['public'] else True
        self.save()
        return self.adminPreferences['public']
    
    def toggleSharedEntries(self):
        self.sharedEntries['enabled'] = False if self.sharedEntries['enabled'] else True
        self.save()
        return self.sharedEntries['enabled']

    def toggleRestrictedAccess(self):
        self.restrictedAccess = False if self.restrictedAccess else True
        self.save()
        return self.restrictedAccess
        
    def toggleNotification(self):
        editor_id=str(g.current_user.id)
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['newEntry']:
                self.editors[editor_id]['notification']['newEntry']=False
            else:
                self.editors[editor_id]['notification']['newEntry']=True
            self.save()
            return self.editors[editor_id]['notification']['newEntry']
        return False

    def toggleExpirationNotification(self):
        editor_id=str(g.current_user.id)
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['expiredForm']:
                self.editors[editor_id]['notification']['expiredForm']=False
            else:
                self.editors[editor_id]['notification']['expiredForm']=True
            self.save()
            return self.editors[editor_id]['notification']['expiredForm']
        return False

    def toggleRequireDataConsent(self):
        self.requireDataConsent = False if self.requireDataConsent else True
        self.save()
        return self.requireDataConsent

    def addLog(self, message, anonymous=False):
        if anonymous:
            actor="system"
        else:
            actor=g.current_user.username if g.current_user else "system"
        logTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log.insert(0, (logTime, actor, message))
        self.save()


class Site(db.Document):
    meta = {'collection': 'sites', 'queryset_class': HostnameQuerySet}
    hostname = db.StringField(required=True)
    port = db.StringField(required=False)
    siteName = db.StringField(required=True)
    scheme = db.StringField(required=False)
    blurb = db.DictField(required=True)
    invitationOnly = db.BooleanField()
    personalDataConsent = db.DictField(required=False)
    smtpConfig = db.DictField(required=True)

    def __init__(self, *args, **kwargs):        
        db.Document.__init__(self, *args, **kwargs)
    
    def __str__(self):
        return pformat({'Site': get_obj_values_as_dict(self)})
    
    @classmethod
    def create(cls):
        hostname=urlparse(request.host_url).hostname
        with open('%s/default_blurb.md' % os.path.dirname(os.path.realpath(__file__)), 'r') as defaultBlurb:
            defaultMD=defaultBlurb.read()
        blurb = {
            'markdown': defaultMD,
            'html': markdown.markdown(defaultMD)
        }
        newSiteData={
            "hostname": hostname,
            "port": None,
            "scheme": urlparse(request.host_url).scheme,
            "blurb": blurb,
            "invitationOnly": True,
            "siteName": "gng-forms!",
            "personalDataConsent": {"markdown": "", "html": "", "enabled": False },
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
        #create the Installation if it doesn't exist
        Installation.get()
        return new_site

    @classmethod
    def find(cls, *args, **kwargs):
        site = cls.findAll(*args, **kwargs).first()
        if not site:
            site=Site.create()
        return site

    @classmethod
    def findAll(cls, *args, **kwargs):
        return cls.objects.ensure_hostname(**kwargs)

    @property
    def host_url(self):
        url= "%s://%s" % (self.scheme, self.hostname)
        if self.port:
            url = "%s:%s" % (url, self.port)
        return url+'/'

    def faviconURL(self):
        path="%s%s_favicon.png" % (app.config['FAVICON_FOLDER'], self.hostname)
        if os.path.exists(path):
            return "/static/images/favicon/%s_favicon.png" % self.hostname
        else:
            return "/static/images/favicon/default-favicon.png"

    def deleteFavicon(self):
        path="%s%s_favicon.png" % (app.config['FAVICON_FOLDER'], self.hostname)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def saveBlurb(self, MDtext):
        self.blurb = {'markdown':escapeMarkdown(MDtext), 'html':markdown2HTML(MDtext)}
        self.save()

    def savePersonalDataConsentText(self, MDtext):
        self.personalDataConsent = {'markdown':escapeMarkdown(MDtext),
                                    'html':markdown2HTML(MDtext),
                                    'enabled': self.personalDataConsent['enabled']}
        self.save()

    def saveSMTPconfig(self, **kwargs):
        self.smtpConfig=kwargs
        self.save()

    def isPersonalDataConsentEnabled(self):
        return self.personalDataConsent["enabled"]
                
    @property
    def totalUsers(self):
        return User.findAll(hostname=self.hostname).count()

    @property
    def admins(self):
        return User.findAll(admin__isAdmin=True, hostname=self.hostname)
    
    @property
    def totalForms(self):
        return Form.findAll(hostname=self.hostname).count()
    
    def toggleInvitationOnly(self):
        self.invitationOnly = False if self.invitationOnly else True
        self.save()
        return self.invitationOnly

    def togglePersonalDataConsentEnabled(self):
        self.personalDataConsent["enabled"] = False if self.personalDataConsent["enabled"] else True
        self.save()
        return self.personalDataConsent["enabled"]

    def toggleScheme(self):
        self.scheme = 'https' if self.scheme=='http' else 'http'
        self.save()
        return self.scheme

    def deleteSite(self):
        users=User.findAll(hostname=self.hostname)
        for user in users:
            user.deleteUser()
        invites = Invite.findAll(hostname=self.hostname)
        for invite in invites:
            invite.delete()
        return self.delete()


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
        return pformat({'Invite': get_obj_values_as_dict(self)})

    @classmethod
    def create(cls, hostname, email, message, admin=False):
        data={
            "hostname": hostname,
            "email": email,
            "message": message,
            "token": createToken(Invite),
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
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, **kwargs):
        return cls.objects.ensure_hostname(**kwargs)
    
    def setToken(self, **kwargs):
        self.invite['token']=createToken(Invite, **kwargs)
        self.save()
        

class Installation(db.Document):
    name = db.StringField(required=True)
    schemaVersion = db.IntField(required=True)
    created = db.StringField(required=True)
   
    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        return pformat({'Installation': get_obj_values_as_dict(self)})

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
        data={  "name": "GNGforms",
                "schemaVersion": app.config['SCHEMA_VERSION'],
                "created": datetime.date.today().strftime("%Y-%m-%d")}
        new_installation=cls(**data)
        new_installation.save()
        return new_installation
    
    def isSchemaUpToDate(self):
        return True if self.schemaVersion == app.config['SCHEMA_VERSION'] else False

    def updateSchema(self):
        if not self.isSchemaUpToDate():
            migratedUpTo=migrateMongoSchema(self.schemaVersion)
            if migratedUpTo:
                self.schemaVersion=migratedUpTo
                self.save()
                return self.schemaVersion
            else:
                return None
        else:
            print('Schema already up to date')
    
    @staticmethod
    def isUser(email):
        return True if User.objects(email=email).first() else False
