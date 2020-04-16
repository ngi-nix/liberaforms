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

from gngforms import app, babel #, models

from flask import Response, redirect, request, url_for
from flask import g, flash #, has_app_context
from flask_babel import gettext
from unidecode import unidecode
import json, time, re, string, random, datetime, csv
from passlib.hash import pbkdf2_sha256
from password_strength import PasswordPolicy
import markdown, re, html
from bs4 import BeautifulSoup
from pprint import pformat


def get_obj_values_as_dict(obj):
    values = {}
    fields = type(obj).__dict__['_fields']
    for key, _ in fields.items():
        value = getattr(obj, key, None)
        values[key] = value
    return values

def make_url_for(function, **kwargs):
    kwargs["_external"]=True
    if 'site' in g:
        kwargs["_scheme"]=g.site.scheme
    return url_for(function, **kwargs)

@babel.localeselector
def get_locale():
    if 'current_user' in g and g.current_user:
        return g.current_user.language
    else:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    response = Response(json_response, 'application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code=status_code
    return response



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

TAG_RE = re.compile(r'<[^>]+>')

def escapeMarkdown(MDtext):
    return TAG_RE.sub('', MDtext)

def markdown2HTML(MDtext):
    MDtext=escapeMarkdown(MDtext)
    return markdown.markdown(MDtext, extensions=['nl2br'])

def stripHTMLTags(text):
    #return TAG_RE.sub(' ', text).strip(' ')
    text=html.unescape(text) 
    soup=BeautifulSoup(text, features="html.parser")
    return soup.get_text()
    
def cleanLabel(text):
    # We should change this to use a whitelist
    text=html.unescape(text) 
    soup=BeautifulSoup(text, features="html.parser")
    for script in soup.find_all("script"):
        script.decompose()
    for style in soup.find_all("style"):
        style.decompose()
    return html.escape(str(soup))


""" ######## Password ######## """

pwd_policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=0,  # need min. 2 uppercase letters
    numbers=0,  # need min. 2 digits
    special=0,  # need min. 2 special characters
    nonletters=1,  # need min. 2 non-letter characters (digits, specials, anything)
)

def hashPassword(password):
    return pbkdf2_sha256.hash(password, rounds=200000, salt_size=16)


def verifyPassword(password, hash):
    return pbkdf2_sha256.verify(password, hash)


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
    while persistentClass.find(token=tokenString):
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
