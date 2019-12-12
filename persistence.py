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

from GNGforms import app, mongo
from GNGforms.utils import *
from GNGforms.migrate import migrateMongoSchema
from bson.objectid import ObjectId
from flask import flash, request, g
from flask_babel import gettext 
from urllib.parse import urlparse
import os, string, random, datetime, json, markdown


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



class User(object):
    user = None

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
        
        user = mongo.db.users.find_one(kwargs)       
        if user:
            instance.user=dict(user)
            return instance
        else:
            return None
    
    def __init__(self, *args, **kwargs):
        pass

    def create(cls, newUserData):
        newUser = mongo.db.users.insert_one(newUserData)
        return User(_id=newUser.inserted_id)

    def findAll(cls, *args, **kwargs):
        if not g.isRootUser:
            kwargs['hostname']=g.site.hostname
        return mongo.db.users.find(kwargs)


    def getNotifyNewFormEmails(cls):
        emails=[]
        criteria={  'hostname':g.site.hostname,
                    'blocked':False,
                    'validatedEmail': True,
                    'admin.isAdmin':True,
                    'admin.notifyNewForm':True}
        admins=mongo.db.users.find(criteria)
        for admin in admins:
            emails.append(admin['email'])
            
        rootUsers=mongo.db.users.find({ 'email': {"$in": app.config['ROOT_USERS']},
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
        admins=mongo.db.users.find(criteria)
        for admin in admins:
            emails.append(admin['email'])
            
        rootUsers=mongo.db.users.find({ 'email': {"$in": app.config['ROOT_USERS']},
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


    @property
    def data(self):
        return self.user

    @property
    def _id(self):
        return self.user['_id']

    @property
    def username(self):
        return self.user['username']

    @property
    def blocked(self):
        return self.user['blocked']

    @property
    def enabled(self):
        if not self.user['validatedEmail']:
            return False
        if self.user['blocked']:
            return False
        return True
    
    @property
    def language(self):
        return self.user['language']

    @language.setter
    def language(self, language):
        self.user['language'] = language

    @property
    def email(self):
        if self.user and 'email' in self.user:
            return self.user['email']
        return None
    
    @email.setter
    def email(self, email):
        self.user['email'] = email
    
    @property
    def hostname(self):
        return self.user['hostname']

    @property
    def token(self):
        return self.user['token']
        
    @property
    def forms(self):
        return Form().findAll(editor=str(self._id))

    @property
    def admin(self):
        return self.user['admin']['isAdmin']
    
    def save(self):
        mongo.db.users.save(self.user)

    def delete(self):
        forms = Form().findAll(author=str(self._id))
        for form in forms:
            mongo.db.forms.remove({'_id': form['_id']})
        return mongo.db.users.remove({'_id': self.user['_id']})

    def isAdmin(self):
        return self.user['admin']['isAdmin']

    def isRootUser(self):
        if self.email in app.config['ROOT_USERS']:
            return True
        return False
    
    def setToken(self, **kwargs):
        self.user['token']=createToken(User, **kwargs)
        self.save()

    def deleteToken(self):
        self.user['token']={}
        self.save()

    def setPassword(self, password):
        self.user['password'] = password
        self.save()

    def toggleBlocked(self):
        if self.isRootUser():
            self.user['blocked']=False
        elif self.blocked:
            self.user['blocked']=False
        else:
            self.user['blocked']=True
        self.save()
        return self.user['blocked']
            
    def toggleAdmin(self):
        if self.isRootUser():
            return self.isAdmin()
        if self.isAdmin():
            self.user['admin']['isAdmin']=False
            mongo.db.users.save(self.user)
        else:
            self.user['admin']['isAdmin']=True
            mongo.db.users.save(self.user)
        return self.isAdmin()

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
        if self.user['admin']['notifyNewUser']:
            self.user['admin']['notifyNewUser'] = False
        else:
            self.user['admin']['notifyNewUser'] = True
        mongo.db.users.save(self.user)
        return self.user['admin']['notifyNewUser']


    """
    send this admin an email when a new form is created
    """
    def toggleNewFormNotification(self):
        if not self.isAdmin():
            return False
        if self.user['admin']['notifyNewForm']:
            self.user['admin']['notifyNewForm'] = False
        else:
            self.user['admin']['notifyNewForm'] = True
        mongo.db.users.save(self.user)
        return self.user['admin']['notifyNewForm']     

    def canViewForm(self, form):
        if str(self._id) in form.editors or self.isAdmin():
            return True
        return False
    
        

class Form(object):
    form = None
    site = None

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
        form = mongo.db.forms.find_one(kwargs)
            
        if form:
            instance.form=dict(form)
            return instance
        else:
            return None


    def __init__(self, *args, **kwargs):
        if self.form and self.form["hostname"]:
            self.site=Site(hostname=self.form["hostname"])
        #pass

    @property
    def data(self):
        return self.form

    @property
    def _id(self):
        return self.form['_id']

    @property
    def author(self):
        return self.form['author']
        
    @property
    def user(self):
        return User(_id=self.form['author'])

    @property
    def editors(self):
        return self.form['editors']
    
    @property
    def slug(self):
        return self.form['slug']

    @property
    def structure(self):
        return self.form['structure']

    @structure.setter
    def structure(self, value):
        self.form['structure'] = value
    
    @property
    def fieldIndex(self):
        return self.form['fieldIndex']
    
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
    def entries(self):
        return self.form['entries']

    @property
    def created(self):
        return self.form['created']

    @property
    def totalEntries(self):
        return len(self.entries)

    @property
    def enabled(self):
        return self.form['enabled']

    def newEditorPreferences(cls):
        return {'notification': {'newEntry': False, 'expiredForm': True}}

    def addEditor(self, editor_id):
        if not editor_id in self.form['editors']:
            self.form['editors'][editor_id]=Form().newEditorPreferences()
            mongo.db.forms.update_one({'_id': self.form['_id']}, {"$set": {"editors": self.form['editors']}})

    def removeEditor(self, editor_id):
        if editor_id == self.author:
            return None
        if editor_id in self.form['editors']:
            del self.form['editors'][editor_id]
            mongo.db.forms.update_one({'_id': self.form['_id']}, {"$set": {"editors": self.form['editors']}})
            return editor_id
        return None

    @property
    def afterSubmitText(self):
        return self.form['afterSubmitText']

    @property
    def hostname(self):
        return self.form['hostname']
    
    @property
    def url(self):
        return "%s%s" % (self.site.host_url, self.slug)  

    def isDataConsentEnabled(self):
        if not self.site.isPersonalDataConsentEnabled():
            return False
        else:
            return self.form["requireDataConsent"]

    @property
    def dataConsent(self):
        return self.site.data['personalDataConsent']['html']

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
        return self.form["expiryConditions"]["fields"]

    def findAll(cls, *args, **kwargs):
        if not g.isRootUser:
            kwargs['hostname']=g.site.hostname
        if 'editor' in kwargs:
            kwargs={"editors.%s" % kwargs["editor"] :{"$exists":True}, **kwargs}
            kwargs.pop('editor')
        return mongo.db.forms.find(kwargs)

    def insert(cls, formData):
        if formData['slug'] in app.config['RESERVED_SLUGS']:
            return None
        newForm = mongo.db.forms.insert_one(formData)
        return Form(_id=newForm.inserted_id)

    def update(self, data):
        mongo.db.forms.update_one({'_id': self.form['_id']}, {"$set": data})
    
    """
    def saveEntry(self, entry):
        mongo.db.forms.update({"_id": self.form["_id"]}, {"$push": {"entries": entry }})
    """
    
    def save(self):
        mongo.db.forms.save(self.form)

    def delete(self):
        return mongo.db.forms.remove({'_id': self.form['_id']})

    def deleteEntries(self):
        self.form["entries"]=[]
        mongo.db.forms.update({"_id": self.form["_id"]}, {"$set": {"entries":[] }})
    
    def isAuthor(self, user):
        return True if self.author == str(user._id) else False
        
    def isEditor(self, user):
        return True if str(user._id) in self.editors else False

    def willExpire(self):
        if self.form["expiryConditions"]["expireDate"]:
            return True
        if self.form["expiryConditions"]["fields"]:
            return True
        return False
        
    @property
    def expired(self):
        return self.form["expired"]

    @expired.setter
    def expired(self, value):
        self.form["expired"]=value

    def hasExpired(self):
        if not self.willExpire():
            return False
        if self.form["expiryConditions"]["expireDate"] and not isFutureDate(self.form["expiryConditions"]["expireDate"]):
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
        if len(self.form['editors']) > 1:
            return True
        return False
    
    def areEntriesShared(self):
        return self.form['sharedEntries']['enabled']
    
    def getSharedEntriesURL(self, part="results"):
        return "%s/%s/%s" % (self.url, part, self.form['sharedEntries']['key'])

    def toggleEnabled(self):
        if self.expired:
            return False
        else:
            self.form['enabled'] = False if self.form['enabled'] else True
            mongo.db.forms.save(self.form)
            return self.form['enabled']

    def toggleSharedEntries(self):
        self.form['sharedEntries']['enabled'] = False if self.form['sharedEntries']['enabled'] else True
        mongo.db.forms.save(self.form)
        return self.form['sharedEntries']['enabled']

    def toggleRestrictedAccess(self):
        self.form['restrictedAccess'] = False if self.form['restrictedAccess'] else True
        mongo.db.forms.save(self.form)
        return self.form['restrictedAccess']
        
    def toggleNotification(self):
        editor_id=str(g.current_user._id)
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['newEntry']:
                self.editors[editor_id]['notification']['newEntry']=False
            else:
                self.editors[editor_id]['notification']['newEntry']=True
            mongo.db.forms.save(self.form)
            return self.editors[editor_id]['notification']['newEntry']
        return False

    def toggleExpirationNotification(self):
        editor_id=str(g.current_user._id)
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['expiredForm']:
                self.editors[editor_id]['notification']['expiredForm']=False
            else:
                self.editors[editor_id]['notification']['expiredForm']=True
            mongo.db.forms.save(self.form)
            return self.editors[editor_id]['notification']['expiredForm']
        return False

    def toggleRequireDataConsent(self):
        self.form['requireDataConsent'] = False if self.form['requireDataConsent'] else True
        mongo.db.forms.save(self.form)
        return self.form['requireDataConsent']

    def addLog(self, message, anonymous=False):
        if anonymous:
            actor="system"
        else:
            actor=g.current_user.username if g.current_user else "system"
        logTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.form['log'].insert(0, (logTime, actor, message))
        self.save()


class Site(object):
    site = None

    def __new__(cls, *args, **kwargs):
        instance = super(Site, cls).__new__(cls)
        if '_id' in kwargs:
            kwargs["_id"] = ObjectId(kwargs['_id'])
        
        searchSiteByKwargs=True if kwargs else False
        if not searchSiteByKwargs:
            kwargs['hostname']=urlparse(request.host_url).hostname
        
        site = mongo.db.sites.find_one(kwargs)
        if site:
            instance.site=dict(site)
            return instance
        elif searchSiteByKwargs:
            return None
            
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
        mongo.db.sites.insert_one(newSiteData)
        #create the Installation if it doesn't exist
        Installation()
        return Site()

    def __init__(self, *args, **kwargs):
        pass
    
    def save(self):
        mongo.db.sites.save(self.site)

    @property
    def data(self):
        return self.site

    @property
    def hostname(self):
        return self.site['hostname']

    @property
    def siteName(self):
        return self.site['siteName'] if 'siteName' in self.site else "gng-forms!"

    @property
    def host_url(self):
        url= "%s://%s" % (self.site['scheme'], self.site['hostname'])
        if self.site['port']:
            url = "%s:%s" % (url, self.site['port'])
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

    @property
    def blurb(self):
        return self.site['blurb']

    def saveBlurb(self, MDtext):
        self.site['blurb'] = {'markdown':escapeMarkdown(MDtext), 'html':markdown2HTML(MDtext)}
        mongo.db.sites.save(self.site)

    def savePersonalDataConsentText(self, MDtext):
        self.site['personalDataConsent'] = {    'markdown':escapeMarkdown(MDtext),
                                                'html':markdown2HTML(MDtext),
                                                'enabled': self.site['personalDataConsent']['enabled']}
        mongo.db.sites.save(self.site)

    @property
    def personalDataConsent(self):
        return self.site['personalDataConsent']

    def saveSMTPconfig(self, **kwargs):
        self.site["smtpConfig"]=kwargs
        self.save()

    @property
    def invitationOnly(self):
        return self.site['invitationOnly']
        
    def isPersonalDataConsentEnabled(self):
        return self.site["personalDataConsent"]["enabled"]
                
    @property
    def totalUsers(self):
        return User().findAll(hostname=self.hostname).count()
        
    @property
    def totalForms(self):
        return Form().findAll(hostname=self.hostname).count()
    
    def toggleInvitationOnly(self):
        self.site["invitationOnly"] = False if self.site["invitationOnly"] else True
        mongo.db.sites.save(self.site)
        return self.site["invitationOnly"]

    def togglePersonalDataConsentEnabled(self):
        self.site["personalDataConsent"]["enabled"] = False if self.site["personalDataConsent"]["enabled"] else True
        mongo.db.sites.save(self.site)
        return self.site["personalDataConsent"]["enabled"]

    def toggleScheme(self):
        self.site["scheme"] = 'https' if self.site["scheme"]=='http' else 'http'
        mongo.db.sites.save(self.site)
        return self.site["scheme"]

    def findAll(cls, *args, **kwargs):
        return mongo.db.sites.find(kwargs)

    def delete(self):
        users = [User(_id=user['_id']) for user in User().findAll(hostname=self.site['hostname'])]
        for user in users:
            user.delete()
        invites = Invite().findAll(hostname=self.site['hostname'])
        for invite in invites:
            mongo.db.invites.remove({'_id': invite['_id']})
        
        return mongo.db.sites.remove({'_id': self.site['_id']})


class Invite(object):
    invite = None

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
            
        invite = mongo.db.invites.find_one(kwargs)
        if invite:
            instance.invite=dict(invite)
            return instance
        else:
            return None
        
    def __init__(self, *args, **kwargs):
        pass


    def create(self, hostname, email, message, admin=False):
        token=createToken(Invite)
        data={
            "hostname": hostname,
            "email": email,
            "message": message,
            "token": token,
            "admin": admin
        }
        mongo.db.invites.insert_one(data)
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
        return mongo.db.invites.find(kwargs)

    def setToken(self, **kwargs):
        self.invite['token']=createToken(Invite, **kwargs)
        self.save()
        
    def delete(self):
        return mongo.db.invites.remove({'_id': self.invite['_id']})


class Installation(object):
    installation = None

    def __new__(cls, *args, **kwargs):
        instance = super(Installation, cls).__new__(cls)
        installation = mongo.db.installation.find_one({"name": "GNGforms"})
            
        if installation:
            instance.installation=dict(installation)
            return instance
        else:
            data={  "name": "GNGforms",
                    "schemaVersion": app.config['SCHEMA_VERSION'],
                    "created": datetime.date.today().strftime("%Y-%m-%d")
                    }
            mongo.db.installation.insert_one(data)
            return Installation()
    
    def __init__(self, *args, **kwargs):
        pass

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
                mongo.db.installation.save(self.installation)
                #mongo.db.installation.update_one({"_id": self.installation["_id"]}, {"$set": {'schemaVersion': migratedUpTo}})
                return self.schemaVersion
            else:
                return None
        else:
            print('Schema already up to date')
