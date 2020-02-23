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
from flask import g, flash, redirect, render_template, url_for
from flask_babel import gettext
from unidecode import unidecode
import time, re, string, random, datetime, csv
from passlib.hash import pbkdf2_sha256
from password_strength import PasswordPolicy
from validate_email import validate_email
import markdown, html.parser
from functools import wraps


""" ######## View wrappers ######## """

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap

def enabled_user_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user and g.current_user.enabled:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.isAdmin:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap

def rootuser_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.isRootUser:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap

def anon_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user:
            return redirect(url_for('index'))
        else:
            return f(*args, **kwargs)
    return wrap

def sanitized_slug_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not ('slug' in kwargs and kwargs['slug'] == sanitizeSlug(kwargs['slug'])):
            if g.current_user:
                flash(gettext("That's a nasty slug!"), 'warning')
            return render_template('page-not-found.html'), 404
        else:
            return f(*args, **kwargs)
    return wrap

def sanitized_key_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not ('key' in kwargs and kwargs['key'] == sanitizeString(kwargs['key'])):
            if g.current_user:
                flash(gettext("That's a nasty key!"), 'warning')
            return render_template('page-not-found.html'), 404
        else:
            return f(*args, **kwargs)
    return wrap

def sanitized_token(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'token' in kwargs and kwargs['token'] != sanitizeTokenString(kwargs['token']):
            if g.current_user:
                flash(gettext("That's a nasty token!"), 'warning')
            return render_template('page_not_found.html'), 404
        else:
            return f(*args, **kwargs)
    return wrap


""" ######## Sanitizers ######## """

def sanitizeString(string):
    string = unidecode(string)
    string = string.replace(" ", "") 
    return re.sub('[^A-Za-z0-9\-]', '', string)

def sanitizeSlug(slug):
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return sanitizeString(slug)

def sanitizeHexidecimal(string): 
    return re.sub('[^A-Fa-f0-9]', '', string)

def isSaneSlug(slug):
    if slug and slug == sanitizeSlug(slug):
        return True
    return False

def sanitizeUsername(username):
    return sanitizeString(username)
    
def isSaneUsername(username):
    if username and username == sanitizeUsername(username):
        return True
    return False

def sanitizeTokenString(string):
    return re.sub('[^a-z0-9]', '', string)
    
def stripHTMLTags(text):
    h = html.parser.HTMLParser()
    text=h.unescape(text)
    return re.sub('<[^<]+?>', '', text)

# remember to remove this from the code because now tags are stripped from Labels at view/preview
def stripHTMLTagsForLabel(text):
    h = html.parser.HTMLParser()
    text=h.unescape(text)
    text = text.replace("<br>","-") # formbuilder generates "<br>"s
    return re.sub('<[^<]+?>', '', text)

def escapeMarkdown(MDtext):
    return re.sub(r'<[^>]*?>', '', MDtext)


def markdown2HTML(MDtext):
    MDtext=escapeMarkdown(MDtext)
    return markdown.markdown(MDtext, extensions=['nl2br'])


""" ######## Password ######## """

policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=0,  # need min. 2 uppercase letters
    numbers=0,  # need min. 2 digits
    special=0,  # need min. 2 special characters
    nonletters=1,  # need min. 2 non-letter characters (digits, specials, anything)
)

def encryptPassword(password):
    return pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)


def verifyPassword(password, hash):
    return pbkdf2_sha256.verify(password, hash)


def isValidPassword(password1, password2):
    if password1 != password2:
        flash(gettext("Passwords do not match"), 'warning')
        return False
    if policy.test(password1):
        flash(gettext("Your password is weak"), 'warning')
        return False
    return True


""" ######## fieldIndex helpers ######## """

def getFieldByNameInIndex(index, name):
    for field in index:
        if 'name' in field and field['name'] == name:
            return field
    return None


""" ######## Tokens ######## """

def getRandomString(length=32):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

"""
Create a unique token.
persistentClass may be a User class, or an Invite class, ..
"""
def createToken(persistentClass, **kwargs):
    tokenString = getRandomString(length=48)
    while persistentClass(token=tokenString):
        tokenString = getRandomString(length=48)
    
    result={'token': tokenString, 'created': datetime.datetime.now()}
    return {**result, **kwargs} 


def isValidToken(tokenData):
    token_age = datetime.datetime.now() - tokenData['created']
    if token_age.total_seconds() > app.config['TOKEN_EXPIRATION']:
        return False
    return True


""" ######## Dates ######## """

def isValidExpireDate(date):
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        return True
    except:
        return False

def isFutureDate(date):
    now=time.time()
    future=int(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%s"))
    return True if future > now else False


""" ######## Others ######## """

def isValidEmail(email):
    if not validate_email(email):
        flash(gettext("Email address is not valid"), 'warning')
        return False
    return True


def writeCSV(form):
    fieldnames=[]
    fieldheaders={}
    for field in form.fieldIndex:
        fieldnames.append(field['name'])
        fieldheaders[field['name']]=field['label']
      
    csv_name='%s/%s.csv' % (app.config['TMP_DIR'], form.slug)
    print(csv_name)
    
    with open(csv_name, mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writerow(fieldheaders)
        for entry in form.data['entries']:
            writer.writerow(entry)

    return csv_name
