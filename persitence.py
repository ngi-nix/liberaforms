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
from flask import flash, request, g
from flask_babel import gettext 
import os, string, random
from urllib.parse import urlparse
import markdown
from .utils import *


import pprint
pp = pprint.PrettyPrinter()


def isNewUserRequestValid(form):   
    if not ('username' in form and 'email' in form and 'password1' in form and 'password2' in form):
        flash(gettext("All fields are required"), 'warning')
        return False
    if form['username'] != sanitizeUsername(form['username']):
        flash(gettext("Username is not valid"), 'warning')
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
        instance = super(User, cls).__new__(cls)
        if not kwargs:
            return instance
        if 'username' in kwargs and kwargs['username'] and kwargs['username'] != sanitizeString(kwargs['username']):
            return None
        if 'token' in kwargs:
            kwargs={"token.token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        if not (g.isRootUser):
            # rootUser can find any user. else only find users registered with this hostname.
            kwargs['hostname']=Site().hostname            

        user = mongo.db.users.find_one(kwargs)
        if user:
            instance.user=dict(user)
            return instance
        else:
            return None
        
    
    def __init__(self, *args, **kwargs):
        pass

    def create(cls, newUser):
        mongo.db.users.insert_one(newUser)
        return User(username=newUser['username'])

    def findAll(cls, *args, **kwargs):
        if not g.isRootUser:
            kwargs['hostname']=Site().hostname
        return mongo.db.users.find(kwargs)


    def getNotifyNewFormEmails(cls):
        emails=[]
        criteria={'hostname':Site().hostname, 'enabled':True, 'admin.isAdmin':True, 'admin.notifyNewForm':True}
        admins=mongo.db.users.find(criteria)
        for admin in admins:
            emails.append(admin['email'])
            
        rootUsers=mongo.db.users.find({'email': {"$in": app.config['ROOT_USERS']}, 'admin.notifyNewForm':True})
        for rootUser in rootUsers:
            if not rootUser['email'] in emails:
                emails.append(rootUser['email'])
        
        return emails


    def getNotifyNewUserEmails(cls):
        emails=[]
        criteria={'hostname':Site().hostname, 'enabled':True, 'admin.isAdmin':True, 'admin.notifyNewUser':True}
        admins=mongo.db.users.find(criteria)
        for admin in admins:
            emails.append(admin['email'])
            
        rootUsers=mongo.db.users.find({'email': {"$in": app.config['ROOT_USERS']}, 'admin.notifyNewUser':True})
        for rootUser in rootUsers:
            if not rootUser['email'] in emails:
                emails.append(rootUser['email'])
        
        return emails


    def isEmailAvailable(cls, email):
        if not isValidEmail(email):
            flash(gettext("Email address is not valid"), 'error')
            return False
        if User(email=email):
            flash(gettext("Email address is not available"), 'error')
            return False
        return True


    @property
    def data(self):
        return self.user

    @property
    def username(self):
        return self.user['username']

    @property
    def enabled(self):
        return self.user['enabled']
    
    @property
    def email(self):
        if self.user and 'email' in self.user:
            return self.user['email']
        return None

    @property
    def language(self):
        return self.user['language']

    @language.setter
    def language(self, language):
        self.user['language'] = language
    
    @email.setter
    def email(self, email):
        self.user['email'] = email
    
    @property
    def hostname(self):
        return self.user['hostname']

    
    def totalForms(self):
        forms = Form().findAll(author=self.username)
        return forms.count()


    def save(self):
        mongo.db.users.save(self.user)


    def delete(self):
        forms = Form().findAll(author=self.username)
        for form in forms:
            mongo.db.forms.remove({'_id': form['_id']})
        return mongo.db.users.remove({'_id': self.user['_id']})


    def isRootUser(self):
        if self.email in app.config['ROOT_USERS']:
            return True
        return False
    
       
    @property
    def token(self):
        return self.user['token']


    def setToken(self, **kwargs):
        self.user['token']=createToken(User, **kwargs)
        self.save()


    def deleteToken(self):
        self.user['token']={}
        self.save()


    def setEnabled(self, value):
        self.user['enabled'] = value
        self.save()


    def setPassword(self, password):
        self.user['password'] = password
        self.save()


    def toggleEnabled(self):
        if self.isRootUser():
            self.user['enabled']=True
        elif self.enabled:
            self.user['enabled']=False
        else:
            self.user['enabled']=True
        self.save()
        return self.user['enabled']


    @property
    def admin(self):
        return self.user['admin']['isAdmin']


    @property
    def defaultAdminSettings(cls):
        return {
            "isAdmin": False,
            "notifyNewUser": False,
            "notifyNewForm": False
        }
            

    def toggleAdmin(self):
        if self.isRootUser():
            return self.admin
        if self.admin:
            self.user['admin']['isAdmin']=False
            mongo.db.users.save(self.user)
        else:
            self.user['admin']['isAdmin']=True
            mongo.db.users.save(self.user)
        return self.admin
    

    """
    send this admin an email when a new user registers at the site
    """
    def toggleNewUserNotification(self):
        if not self.user['admin']:
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
        if not self.user['admin']:
            return False
        if self.user['admin']['notifyNewForm']:
            self.user['admin']['notifyNewForm'] = False
        else:
            self.user['admin']['notifyNewForm'] = True
        mongo.db.users.save(self.user)
        return self.user['admin']['notifyNewForm']



    def setValidatedEmail(self, value):
        self.user['validatedEmail'] = value
        self.save()
        

    def canViewForm(self, form):
        if self.username == form.author or self.admin:
            return True
        flash(gettext("Permission needed to view form"), 'warning')
        return False
    
        

class Form(object):
    form = None

    def __new__(cls, *args, **kwargs):
        instance = super(Form, cls).__new__(cls)
        if not kwargs:
            return instance
        if 'slug' in kwargs and kwargs['slug'] and kwargs['slug'] != sanitizeSlug(kwargs['slug']):
            return None
        if not g.isRootUser:
            # rootUser can find any form. else only find forms created at this hostname.
            kwargs['hostname']=Site().hostname
            
        form = mongo.db.forms.find_one(kwargs)
        if form:
            instance.form=dict(form)
            return instance
        else:
            return None


    def __init__(self, *args, **kwargs):
        pass

    @property
    def data(self):
        return self.form

    @property
    def author(self):
        return self.form['author']

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

    """
    @fieldIndex.setter
    def fieldIndex(self, value):
        self.form['fieldIndex'] = value
    """
    
    @property
    def entries(self):
        return self.form['entries']

    @property
    def created(self):
        return self.form['created']


    def findAll(cls, *args, **kwargs):
        if not g.isRootUser:
            kwargs['hostname']=Site().hostname
        return mongo.db.forms.find(kwargs)


    def toggleEnabled(self):
        if self.form['enabled']:
            self.form['enabled']=False
        else:
            self.form['enabled']=True
        mongo.db.forms.save(self.form)
        return self.form['enabled']


    def toggleNotification(self):
        if self.form['notification']['newEntry']:
            self.form['notification']['newEntry']=False
        else:
            self.form['notification']['newEntry']=True
        mongo.db.forms.save(self.form)
        return self.form['notification']['newEntry']


    def insert(self, formData):
        if formData['slug'] in app.config['RESERVED_SLUGS']:
            return None # just in case
        return mongo.db.forms.insert_one(formData)

    def update(self, data):
        mongo.db.forms.update_one({'slug':self.slug}, {"$set": data})
    
    def saveEntry(self, entry):
        mongo.db.forms.update({"_id": self.form["_id"]}, {"$push": {"entries": entry }})

    def delete(self):
        return mongo.db.forms.remove({'_id': self.form['_id']})

    def deleteEntries(self):
        mongo.db.forms.update({"_id": self.form["_id"]}, {"$set": {"entries":[] }})
    
    @property
    def totalEntries(self):
        return len(self.entries)


    @property
    def enabled(self):
        return self.form['enabled']

    @property
    def notification(self):
        return self.form['notification']

    @property
    def afterSubmitText(self):
        return self.form['afterSubmitText']

    @property
    def hostname(self):
        return self.form['hostname']
    
    @property
    def url(self):
        formSite=Site(hostname=self.hostname)
        return "%s%s" % ( formSite.host_url, self.slug)  

    @property
    def lastEntryDate(self):
        if self.entries:
            last_entry = self.entries[-1] 
            return last_entry["created"]
        else:
            return ""

            
    def isAuthor(self, user):
        if self.author != user.username:
            return False
        return True


    def isPublic(self):
        if not self.enabled:
            return False
        if not User(username=self.author).enabled:
            return False
        return True



        

class Site(object):
    site = None

    def __new__(cls, *args, **kwargs):
        instance = super(Site, cls).__new__(cls)
        
        if 'hostname' in kwargs:
            searchSiteByHostname=True
        else:
            kwargs['hostname']=urlparse(request.host_url).hostname
            searchSiteByHostname=False

        site = mongo.db.sites.find_one(kwargs)
        if site:
            instance.site=dict(site)
            return instance
        else:
            if searchSiteByHostname:
                return None
            
            # this Site is new. Let's create it!
            hostname=urlparse(request.host_url).hostname
        
            # create a new site with this hostname
            with open('%s/default_blurb.md' % os.path.dirname(os.path.realpath(__file__)), 'r') as defaultBlurb:
                defaultMD=defaultBlurb.read()
            blurb = {
                'markdown': defaultMD,
                'html': markdown.markdown(defaultMD)
            }
            
            newSiteData={
                "hostname": hostname,
                "scheme": urlparse(request.host_url).scheme,
                "blurb": blurb,
                "invitationOnly": True,
                "noreplyEmailAddress": "no-reply@%s" % hostname
            }
            mongo.db.sites.insert_one(newSiteData)
            return Site()

    
    def save(self):
        mongo.db.sites.save(self.site)


    def __init__(self, *args, **kwargs):
        pass


    @property
    def data(self):
        return self.site

    @property
    def hostname(self):
        return self.site['hostname']

    @property
    def host_url(self):
        return "%s://%s/" %(self.site['scheme'], self.site['hostname'])

    @property
    def blurb(self):
        return self.site['blurb']

    def saveBlurb(self, MDtext):
        self.site['blurb'] = {'markdown':escapeMarkdown(MDtext), 'html':markdown2HTML(MDtext)}
        mongo.db.sites.save(self.site)

    @property
    def noreplyEmailAddress(self):
        return self.site['noreplyEmailAddress']

    @noreplyEmailAddress.setter
    def noreplyEmailAddress(self, email):
        self.site["noreplyEmailAddress"] = email
        mongo.db.sites.save(self.site)

    @property
    def invitationOnly(self):
        return self.site['invitationOnly']
        
    def toggleInvitationOnly(self):
        if self.site["invitationOnly"]:
            self.site["invitationOnly"]=False
        else:
            self.site["invitationOnly"]=True
        mongo.db.sites.save(self.site)
        return self.site["invitationOnly"]

    def findAll(cls, *args, **kwargs):
        return mongo.db.sites.find(kwargs)

    def delete(self):
        users = User().findAll(hostname=self.site['hostname'])
        for user in users:
            mongo.db.users.remove({'_id': user['_id']})
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
        if not (g.isRootUser or 'hostname' in kwargs):
            kwargs['hostname']=Site().hostname
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
    def token(self):
        if self.invite:
            return self.invite['token']
        return None

    def findAll(cls, *args, **kwargs):
        if not g.isRootUser:
            kwargs['hostname']=Site().hostname
        return mongo.db.invites.find(kwargs)

    def setToken(self, **kwargs):
        self.invite['token']=createToken(Invite, **kwargs)
        self.save()
        
    def delete(self):
        return mongo.db.invites.remove({'_id': self.invite['_id']})
