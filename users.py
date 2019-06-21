from formbuilder import app, mongo
from flask import flash
import string, random, datetime
from validate_email import validate_email
from .utils import *
from .forms import *


import pprint
pp = pprint.PrettyPrinter()


def createUser(newUser):
    mongo.db.users.insert_one(newUser)
    return User(username=newUser['username'])
    

def isNewUserRequestValid(form):   
    if not ('username' in form and 'email' in form and 'password1' in form and 'password2' in form):
        flash("All fields are required", 'info')
        return False
    if User(username=form['username']):
        flash("username not available", 'info')
        return False
    if not User().isEmailValid(form['email']):
        return False
    if not isValidPassword(form['password1'], form['password2']):
        return False
    return True


class User(object):
    user = None

    def __new__(cls, *args, **kwargs):
        instance = super(User, cls).__new__(cls)
        if kwargs:
            if 'token' in kwargs:
                user = mongo.db.users.find_one({"token.token": kwargs['token']})
            else:
                user = mongo.db.users.find_one(kwargs)
            if user:
                instance.user=dict(user)
            else:
                return None
        return instance

    
    def __init__(self, *args, **kwargs):
        pass


    def findAll(cls):
        return mongo.db.users.find()


    def isEmailValid(cls, email):
        if not validate_email(email):
            flash("email address is not valid", 'info')
            return False
        if User(email=email):
            flash("email address not available", 'info')
            return False
        return True


    @property
    def data(self):
        return self.user


    def hasTokenExpired(self):
        token_age = datetime.datetime.now() - self.user['token']['created']
        if token_age.total_seconds() > app.config['TOKEN_EXPIRATION']:
            return True
        return False


    def setToken(self):
        token = getRandomString(length=48)
        while mongo.db.users.find_one({"token.token": token}):
            print('token found')
            token = getRandomString(length=48)
        self.user['token']={'token': token, 'created': datetime.datetime.now()}
        mongo.db.users.save(self.user)


    def deleteToken(self):
        self.user['token']={}
        mongo.db.users.save(self.user)


    def setEnabled(self, value):
        self.user['enabled'] = value
        mongo.db.users.save(self.user)


    def toggleEnabled(self):
        if self.user['enabled']:
            self.user['enabled']=False
        else:
            self.user['enabled']=True
        mongo.db.users.save(self.user)
        return self.user['enabled']


    def setValidatedEmail(self, value):
        self.user['validatedEmail'] = value
        mongo.db.users.save(self.user)
        
        
    def authoredFormsCount(self):
        forms = findForms(author=self.user['username'])
        return forms.count()
