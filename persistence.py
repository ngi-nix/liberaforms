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
from bson.objectid import ObjectId
from flask import flash, request, g
from flask_babel import gettext 
from urllib.parse import urlparse
import os, string, random, datetime, json, markdown

from mongoengine import queryset_manager

import pprint
pp = pprint.PrettyPrinter()



def isNewUserRequestValid(form):   
    if not ('username' in form and 'email' in form and 'password1' in form and 'password2' in form):
        flash(gettext("All fields are required"), 'warning')
        return False
    if form['username'] != sanitizeUsername(form['username']):
        flash(gettext("Username is not valid"), 'warning')
        return False
    if form['username'] in app.config['RESERVED_USERNAMES']:
        flash(gettext("Username is not available"), 'warning')
        return False
    user = User(username=form['username'])
    if user:
        flash(gettext("Username is not available"), 'warning')
        return False
    if not User().isEmailAvailable(form['email']):
        return False
    if not isValidPassword(form['password1'], form['password2']):
        return False
    return True



class User(db.Document):
    meta = {'collection': 'users'}
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

    def get_obj_values_as_dict(self):
        values = {}
        fields = type(self).__dict__['_fields']
        for key, _ in fields.items():
            value = getattr(self, key, None)
            values[key] = value
        return values

    """
    def __new__(cls, *args, **kwargs):
        if 'username' in kwargs and not isSaneUsername(kwargs['username']):
            return None
            
        instance = super(User, cls).__new__(cls)
        if not kwargs:
            return instance
           
        if '_id' in kwargs:
            kwargs['_id'] = ObjectId(kwargs['_id'])
        if 'token' in kwargs:
            kwargs={"token.token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        if not ('hostname' in kwargs or g.isRootUser):
            kwargs['hostname']=g.site.hostname
        
        user = db.users.find_one(kwargs)       
        if user:
            instance.user=dict(user)
            return instance
        else:
            return None
    """
    
    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)

    @queryset_manager
    def objects(cls, queryset):
        if not g.isRootUser:
            return queryset.filter(hostname=g.site.hostname)
        else:
            return queryset
    
    @classmethod
    def create(cls, newUserData):
        newUser = db.users.insert_one(newUserData)
        return User(id=newUser.inserted_id)

    @classmethod
    def find(cls, **kwargs):
        print('kw-find-user: %s' % kwargs)
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, *args, **kwargs):
        if 'token' in kwargs:
            #kwargs={"token.token": kwargs['token'], **kwargs}
            kwargs={"token__token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        print('kw-findall-user: %s' % kwargs)
        return cls.objects(**kwargs)

    @classmethod
    def getNotifyNewFormEmails(cls):
        emails=[]
        criteria={  'hostname':g.site.hostname,
                    'blocked':False,
                    'validatedEmail': True,
                    'admin.isAdmin':True,
                    'admin.notifyNewForm':True}
        #admins=db.users.find(criteria)
        admins=User.objects(criteria)
        for admin in admins:
            emails.append(admin['email'])
            
        #rootUsers=db.users.find({ 'email': {"$in": app.config['ROOT_USERS']},
        rootUsers=User.objects({'email': {"$in": app.config['ROOT_USERS']},
                                'admin.notifyNewForm':True})
        for rootUser in rootUsers:
            if not rootUser['email'] in emails:
                emails.append(rootUser['email'])
        return emails

    def getNotifyNewUserEmails(cls):
        emails=[]
        criteria={  'hostname':g.site.hostname,
                    'blocked':False,
                    'validatedEmail': True,
                    'admin.isAdmin':True,
                    'admin.notifyNewUser':True}
        #admins=db.users.find(criteria)
        admins=User.objects(criteria)
        for admin in admins:
            emails.append(admin['email'])
            
        #rootUsers=db.users.find({ 'email': {"$in": app.config['ROOT_USERS']},
        rootUsers=User.objects({'email': {"$in": app.config['ROOT_USERS']},
                                'admin.notifyNewUser':True})
        for rootUser in rootUsers:
            if not rootUser['email'] in emails:
                emails.append(rootUser['email'])
        return emails

    def isEmailAvailable(cls, email):
        if not isValidEmail(email):
            flash(gettext("Email address is not valid"), 'warning')
            return False
        if User(email=email):
            flash(gettext("Email address is not available"), 'warning')
            return False
        return True

    
    """
    @property
    def _id(self):
        return self.user['_id']
    """


    @property
    def enabled(self):
        if not self.validatedEmail:
            return False
        if self.blocked:
            return False
        return True
    
    def set_language(self, language):
        self.language = language

    """
    !!! Where is this used???
    @property
    def email(self):
        if self.user and 'email' in self.user:
            return self.user['email']
        return None
    """
    
    def set_email(self, email):
        self.email = email
        
    @property
    def forms(self):
        #return [Form(_id=form['_id']) for form in Form().findAll(editor=str(self.id))]
        return Form.findAll(editor=str(self.id))

    
    def isAdmin(self):
        return self.admin#['isAdmin']
    
    def delete(self):
        forms = Form.findAll(author=str(self.id))
        for form in forms:
            db.forms.remove({'id': form.id})
        return db.users.remove({'id': self.id})

    """
    def isAdmin(self):
        return self.admin# ['isAdmin']
    """
    
    def isRootUser(self):
        if self.email in app.config['ROOT_USERS']:
            return True
        return False
    
    def setToken(self, **kwargs):
        self.token=createToken(User, **kwargs)
        self.save()

    def deleteToken(self):
        self.token={}
        self.save()

    def setPassword(self, password):
        self.password = password
        self.save()

    def toggleBlocked(self):
        if self.isRootUser():
            self.blocked=False
        elif self.blocked:
            self.blocked=False
        else:
            self.blocked=True
        self.save()
        return self.blocked
            
    def toggleAdmin(self):
        if self.isRootUser():
            return self.isAdmin()
        if self.isAdmin():
            self.admin['isAdmin']=False
            self.save()
        else:
            self.admin['isAdmin']=True
            self.save()
        return self.isAdmin()

    @classmethod
    def defaultAdminSettings(cls):
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
        if self.admin['notifyNewUser']:
            self.admin['notifyNewUser'] = False
        else:
            self.admin['notifyNewUser'] = True
        self.save()
        return self.admin['notifyNewUser']


    """
    send this admin an email when a new form is created
    """
    def toggleNewFormNotification(self):
        if not self.isAdmin():
            return False
        if self.admin['notifyNewForm']:
            self.admin['notifyNewForm'] = False
        else:
            self.admin['notifyNewForm'] = True
        self.save()
        return self.admin['notifyNewForm']    

    def canViewForm(self, form):
        if str(self.id) in form.editors or self.isAdmin():
            return True
        return False
    
        

class Form(db.Document):
    meta = {'collection': 'forms'}
    created = db.StringField(required=True)
    hostname = db.StringField(required=True)
    slug = db.StringField(required=True)
    author = db.StringField(required=True)
    editors = db.DictField(required=True)
    postalCode = db.StringField(required=False)
    enabled = db.BooleanField()
    expired = db.BooleanField()
    expiryConditions = db.DictField(required=False)
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


    """
    def __new__(cls, *args, **kwargs):
        if 'slug' in kwargs and not isSaneSlug(kwargs['slug']):
            return None

        instance = super(Form, cls).__new__(cls)
        if not kwargs:
            return instance

        if '_id' in kwargs:
            kwargs["_id"] = ObjectId(kwargs['_id'])
        if 'editor' in kwargs:
            kwargs={"editors.%s" % kwargs["editor"]: {"$exists":True}, **kwargs}
            kwargs.pop('editor')
        if 'key' in kwargs:
            kwargs={"sharedEntries.key": kwargs['key'], **kwargs}
            kwargs.pop('key')
        if not ('hostname' in kwargs or g.isRootUser):
            kwargs['hostname']=g.site.hostname
        #print(kwargs)
        form = db.forms.find_one(kwargs)
            
        if form:
            instance.form=dict(form)
            return instance
        else:
            return None
    """

    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)
        self.site=Site.objects(hostname=self.hostname).first()

    @queryset_manager
    def objects(cls, queryset):
        if not g.isRootUser:
            return queryset.filter(hostname=g.site.hostname)
        else:
            return queryset
    
    def get_obj_values_as_dict(self):
        values = {}
        fields = type(self).__dict__['_fields']
        for key, _ in fields.items():
            value = getattr(self, key, None)
            values[key] = value
        return values

    def changeAuthor(self, new_author):
        if new_author.enabled:
            if self.author in self.editors:
                del self.editors[self.author]
            self.author=str(new_author.id)
            if self.addEditor(new_author):
                self.save()
                return True
        return False

    @property
    def user(self):
        return User.objects(id=self.author).first()
    
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

    def is_enabled(self):
        if not self.adminPreferences['public']:
            return False
        return self.enabled

    def newEditorPreferences(cls):
        return {'notification': {'newEntry': False, 'expiredForm': True}}

    def addEditor(self, editor):
        if not editor.enabled:
            return False
        editor_id=str(editor.id)
        if not editor_id in self.form['editors']:
            self.form['editors'][editor_id]=Form().newEditorPreferences()
            db.forms.update_one({'_id': self.form['_id']}, {"$set": {"editors": self.form['editors']}})
            return True
        return False

    def removeEditor(self, editor_id):
        if editor_id == self.author:
            return None
        if editor_id in self.form['editors']:
            del self.form['editors'][editor_id]
            db.forms.update_one({'_id': self.form['_id']}, {"$set": {"editors": self.form['editors']}})
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
    def find(cls, **kwargs):
        print('kw-find-form: %s' % kwargs)
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, **kwargs):
        if 'editor' in kwargs:
            kwargs={"__raw__": {'editors.%s' % kwargs["editor"]: {'$exists': True}}, **kwargs}
            kwargs.pop('editor')
        if 'key' in kwargs:
            kwargs={"sharedEntries__key": kwargs['key'], **kwargs}
            kwargs.pop('key')
        print('kw-findall-form: %s' % kwargs)
        return cls.objects(**kwargs)

    @classmethod
    def insert(cls, formData):
        if formData['slug'] in app.config['RESERVED_SLUGS']:
            return None
        #newForm = db.forms.insert_one(formData)
        #return Form(_id=newForm.inserted_id)
        new_form=Form(formData)
        new_form.save()
        return new_form

    def update(self, data):
        db.forms.update_one({'_id': self.form['_id']}, {"$set": data})
    
    """
    def saveEntry(self, entry):
        db.forms.update({"_id": self.form["_id"]}, {"$push": {"entries": entry }})
    """
    
    def delete(self):
        return db.forms.remove({'_id': self.form['_id']})

    def deleteEntries(self):
        self.entries=[]
        db.forms.update({"_id": self.form["_id"]}, {"$set": {"entries":[] }})
    
    def isAuthor(self, user):
        return True if self.author == str(user.id) else False
        
    def isEditor(self, user):
        return True if str(user.id) in self.editors else False

    def getEditors(self):
        editors=[]
        print(self.editors)
        for editor_id in self.editors:
            print (editor_id)
            #user=User.objects(id=editor_id).first()
            user=User.find(id=editor_id)
            if user:
                editors.append(user)
            else:
                # remove editor_id from self.editors
                pass
        for edito in editors:
            print("%s - %s" % (edito.id,edito.username))
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
        if self.expired:
            return False
        if not self.enabled:
            return False
        if not self.user.enabled:
            return False
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
    meta = {'collection': 'sites'}
    hostname = db.StringField(required=True)
    port = db.StringField(required=False)
    siteName = db.StringField(required=False)
    scheme = db.StringField(required=False)
    blurb = db.DictField(required=True)
    invitationOnly = db.BooleanField()
    personalDataConsent = db.DictField(required=False)
    smtpConfig = db.DictField(required=False)

    
    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(hostname=urlparse(request.host_url).hostname)

    
    """
    def __new__(cls, *args, **kwargs):
        instance = super(Site, cls).__new__(cls)
        if '_id' in kwargs:
            kwargs["_id"] = ObjectId(kwargs['_id'])

        #searchSiteByKwargs=True if kwargs else False
        #if not searchSiteByKwargs:
        #    kwargs['hostname']=urlparse(request.host_url).hostname
        
        #site = db.sites.find_one(kwargs)
        
        #if not 'hostname' in kwargs:
       #     kwargs['hostname']=urlparse(request.host_url).hostname
       #     site = Site.objects(hostname=kwargs['hostname'])
       #     if site:
       #         return instance
       #     else:
       #         return None
            
        #ºreturn instance
    """
    """
        site = Site.objects(hostname=kwargs['hostname'])
        if site:
            instance.site=dict(site)
            return instance
            
        #elif searchSiteByKwargs:
        #    return None
    """
    """       
        # this Site is new. Let's create a site with this hostname
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
        db.sites.insert_one(newSiteData)
        #create the Installation if it doesn't exist
        #Installation()
        return Site()
    """

    def __init__(self, *args, **kwargs):        
        db.Document.__init__(self, *args, **kwargs)

    def __repr__(self):
        print("<Site=%s" % self.hostname)

    def get_obj_values_as_dict(self):
        values = {}
        fields = type(self).__dict__['_fields']
        for key, _ in fields.items():
            value = getattr(self, key, None)
            values[key] = value
        return values
    
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
        new_site=Site(newSiteData)
        new_site.save()
        #create the Installation if it doesn't exist
        #Installation()
        return new_site
      
   
    """
    @property
    def siteName(self):
        return self.site['siteName'] if 'siteName' in self.site else "gng-forms!"
    """

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
        db.sites.save(self.site)

    def savePersonalDataConsentText(self, MDtext):
        self.personalDataConsent = {   'markdown':escapeMarkdown(MDtext),
                                    'html':markdown2HTML(MDtext),
                                    'enabled': self.personalDataConsent['enabled']}
        self.save()


    def saveSMTPconfig(self, **kwargs):
        self.site["smtpConfig"]=kwargs
        self.save()

    def isPersonalDataConsentEnabled(self):
        return self.personalDataConsent["enabled"]
                
    @property
    def totalUsers(self):
        return User.objects(hostname=self.hostname).count()
        #return User().findAll(hostname=self.hostname).count()

    @property
    def admins(self):
        criteria={"admin.isAdmin": True, 'hostname': self.hostname}
        return User.objects(**criteria)
        #return [User(_id=user['_id']) for user in db.users.find(criteria)]
    
    @property
    def totalForms(self):
        return Form(hostname=self.hostname).count()
        #return Form().findAll(hostname=self.hostname).count()
    
    def toggleInvitationOnly(self):
        self.invitationOnly = False if self.invitationOnly else True
        self.save()
        return self.invitationOnly

    def togglePersonalDataConsentEnabled(self):
        self.personalDataConsent["enabled"] = False if selfpersonalDataConsent["enabled"] else True
        self.save()
        return self.personalDataConsent["enabled"]

    def toggleScheme(self):
        self.scheme = 'https' if self.scheme=='http' else 'http'
        self.save()
        return self.scheme

    @classmethod
    def findAll(cls):
        return Site.objects
        #return db.sites.find(kwargs)

    def delete(self):
        users = [User(_id=user['_id']) for user in User().findAll(hostname=self.site['hostname'])]
        for user in users:
            user.delete()
        invites = Invite().findAll(hostname=self.site['hostname'])
        for invite in invites:
            db.invites.remove({'_id': invite['_id']})
        
        return db.sites.remove({'_id': self.site['_id']})


class Invite(db.Document):
    

    def __new__(cls, *args, **kwargs):
        instance = super(Invite, cls).__new__(cls)
        if not kwargs:
            return instance
        if '_id' in kwargs:
            kwargs["_id"] = ObjectId(kwargs['_id'])
        if not ('hostname' in kwargs or g.isRootUser):
            kwargs['hostname']=g.site.hostname
        if 'token' in kwargs:
            kwargs={"token.token": kwargs['token'], **kwargs}
            kwargs.pop('token') 
            
        invite = db.invites.find_one(kwargs)
        if invite:
            instance.invite=dict(invite)
            return instance
        else:
            return None
        
    def __init__(self, *args, **kwargs):
        pass


    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(hostname=urlparse(request.host_url).hostname)

    def create(self, hostname, email, message, admin=False):
        token=createToken(Invite)
        data={
            "hostname": hostname,
            "email": email,
            "message": message,
            "token": token,
            "admin": admin
        }
        db.invites.insert_one(data)
        return Invite(hostname=hostname, token=token['token'])

    @property
    def data(self):
        return self.invite

    @property
    def _id(self):
        return self.invite['_id']

    @property
    def email(self):
        return self.invite['email']

    @property
    def token(self):
        if self.invite:
            return self.invite['token']
        return None

    def findAll(cls, *args, **kwargs):
        if not g.isRootUser:
            kwargs['hostname']=g.site.hostname
        return db.invites.find(kwargs)

    def setToken(self, **kwargs):
        self.invite['token']=createToken(Invite, **kwargs)
        self.save()
        
    def delete(self):
        return db.invites.remove({'_id': self.invite['_id']})


class Installation(db.Document):

    def __new__(cls, *args, **kwargs):
        instance = super(Installation, cls).__new__(cls)
        installation = db.installation.find_one({"name": "GNGforms"})
            
        if installation:
            instance.installation=dict(installation)
            return instance
        else:
            data={  "name": "GNGforms",
                    "schemaVersion": app.config['SCHEMA_VERSION'],
                    "created": datetime.date.today().strftime("%Y-%m-%d")
                    }
            db.installation.insert_one(data)
            return Installation()
    
    def __init__(self, *args, **kwargs):
        pass

    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(hostname=urlparse(request.host_url).hostname)


    @property
    def data(self):
        return self.installation

    @property
    def schemaVersion(self):
        return self.installation['schemaVersion']
        
    def isSchemaUpToDate(self):
        if self.schemaVersion != app.config['SCHEMA_VERSION']:
            return False
        return True

    def updateSchema(self):
        if not self.isSchemaUpToDate():
            migratedUpTo=migrateMongoSchema(self.schemaVersion)
            if migratedUpTo:
                self.installation['schemaVersion']=migratedUpTo
                db.installation.save(self.installation)
                #db.installation.update_one({"_id": self.installation["_id"]}, {"$set": {'schemaVersion': migratedUpTo}})
                return self.schemaVersion
            else:
                return None
        else:
            print('Schema already up to date')
            
    @classmethod
    def isUser(self, email):
        if db.users.find_one({'email':email}):
            return True
        else:
            return False
