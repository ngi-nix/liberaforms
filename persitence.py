"""
“Copyright 2019 La Coordinadora d’Entitats la Lleialtat Santsenca”

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

from formbuilder import app, mongo
from flask import flash, request, g
import string, random, datetime
from urllib.parse import urlparse
from .utils import *


import pprint
pp = pprint.PrettyPrinter()


def createUser(newUser):
    mongo.db.users.insert_one(newUser)
    return User(username=newUser['username'])


def isNewUserRequestValid(form):   
    if not ('username' in form and 'email' in form and 'password1' in form and 'password2' in form):
        flash("All fields are required", 'warning')
        return False
    if form['username'] != sanitizeString(form['username']):
        flash("Username is not valid", 'warning')
        return False
    user = User(username=form['username'])
    if user:
        flash("Username is not available", 'warning')
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
        if 'token' in kwargs:
            kwargs={"token.token": kwargs['token'], **kwargs}
            kwargs.pop('token') 
        if not (g.current_user and g.current_user.isRootUser()):
            # rootUser can find any user. else only find users registered with this hostname.
            kwargs['hostname']=urlparse(request.host_url).hostname

        user = mongo.db.users.find_one(kwargs)
        if user:
            instance.user=dict(user)
            return instance
        else:
            return None
        
    
    def __init__(self, *args, **kwargs):
        pass



    def findAll(cls, *args, **kwargs):
        if not g.current_user.isRootUser():
            kwargs['hostname']=g.hostname
        return mongo.db.users.find(kwargs)
      
    

    def isEmailAvailable(cls, email):
        if not isValidEmail(email):
            flash("Email address is not valid", 'error')
            return False
        if User(email=email):
            flash("Email address is not available", 'error')
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
        
    @email.setter
    def email(self, email):
        self.user['email'] = email
    
    @property
    def hostname(self):
        return self.user['hostname']

    
    def totalForms(self):
        print("username: %s" % self.username)
        forms = Form().findAll(author=self.username)
        return forms.count()


    def save(self):
        mongo.db.users.save(self.user)


    def isRootUser(self):
        if self.email in app.config['ROOT_ADMINS']:
            return True
        return False
    

    @property
    def token(self):
        return self.user['token']


    def hasTokenExpired(self):
        token_age = datetime.datetime.now() - self.token['created']
        if token_age.total_seconds() > app.config['TOKEN_EXPIRATION']:
            return True
        return False


    def setToken(self, *args, **kwargs):
        token = getRandomString(length=48)
        while mongo.db.users.find_one({"token.token": token}):
        #while User(token=token):
            print('token found')
            token = getRandomString(length=48)
        self.user['token']={'token': token, 'created': datetime.datetime.now(), **kwargs}
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
        if self.user and 'admin' in self.user:
            return self.data['admin']
        else:
            return False


    def toggleAdmin(self):
        if self.isRootUser():
            self.user['admin']=True
        elif self.admin:
            self.user['admin']=False
        else:
            self.user['admin']=True
        mongo.db.users.save(self.user)
        return self.admin
        

    def setValidatedEmail(self, value):
        self.user['validatedEmail'] = value
        self.save()
        

    def canViewForm(self, form):
        if self.username == form.author or self.admin:
            return True
        flash("Permission needed to view form", 'warning')
        return False
    
    
    def canEditForm(self, form):
        if self.username == form.author:
            return True
        return False
        



class Form(object):
    form = None

    def __new__(cls, *args, **kwargs):
        instance = super(Form, cls).__new__(cls)
        if not kwargs:
            return instance
        if not (g.current_user and g.current_user.isRootUser()):
            # rootUser can find any form. else only find forms created at this hostname.
            kwargs['hostname']=urlparse(request.host_url).hostname
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
        if not g.current_user.isRootUser():
            kwargs['hostname']=g.hostname
        return mongo.db.forms.find(kwargs)


    def toggleEnabled(self):
        if self.form['enabled']:
            self.form['enabled']=False
        else:
            self.form['enabled']=True
        mongo.db.forms.save(self.form)
        return self.form['enabled']


    def insert(self, formData):
        mongo.db.forms.insert_one(formData)

    def update(self, data):
        mongo.db.forms.update_one({'slug':self.slug}, {"$set": data})
    
    def saveEntry(self, entry):
        mongo.db.forms.update({ "_id": self.form["_id"] }, {"$push": {"entries": entry }})

    @property
    def totalEntries(self):
        return len(self.entries)


    @property
    def enabled(self):
        return self.form['enabled']


    @property
    def hostname(self):
        return self.form['hostname']
        

    @property
    def lastEntryDate(self):
        if self.entries:
            last_entry = self.entries[-1] 
            last_entry_date = last_entry["created"]
        else:
            last_entry_date = ""

            
    def isAuthor(self, user):
        if self.author != user.username:
            return False
        return True


    def isAvailable(self):
        if not self.enabled:
            return False
        if not User(username=self.author).enabled:
            return False
        return True



        

class Site(object):
    site = None

    def __new__(cls, *args, **kwargs):
        instance = super(Site, cls).__new__(cls)
        if kwargs:
            site = mongo.db.forms.find_one(kwargs)
            if site:
                instance.site=dict(site)
            else:
                return None
        return instance

    
    def __init__(self, *args, **kwargs):
        pass
