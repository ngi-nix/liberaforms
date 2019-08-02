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
from flask import flash
from flask_babel import gettext
from unidecode import unidecode
import re, string, random, datetime, csv
from passlib.hash import pbkdf2_sha256
from password_strength import PasswordPolicy
from validate_email import validate_email
import markdown

policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=0,  # need min. 2 uppercase letters
    numbers=0,  # need min. 2 digits
    special=0,  # need min. 2 special characters
    nonletters=1,  # need min. 2 non-letter characters (digits, specials, anything)
)



def sanitizeSlug(slug):
    slug = slug.lower()
    slug = slug.replace(" ", "-") 
    return sanitizeString(slug)


def sanitizeString(string):
    string = unidecode(string)
    string = string.replace(" ", "") 
    return re.sub('[^A-Za-z0-9\-]', '', string)


def stripHTMLTags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)


def encryptPassword(password):
    return pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)


def verifyPassword(password, hash):
    return pbkdf2_sha256.verify(password, hash)
    

def getRandomString(length=32):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def getFieldByNameInIndex(index, name):
    for field in index:
        if 'name' in field and field['name'] == name:
            return field
    return None


def removeHTMLFromLabels(fieldIndex):
    """
    formbuilder adds HTML tags to labels like '<br>' or '<div></div>'.
    The tags (formatted lables) are good when rendering the form but we do not want them included in CSV column headers.
    This function is called when viewing form entry data.
    """
    result=[]
    for field in fieldIndex:
        result.append({'label': stripHTMLTags(field['label']), 'name': field['name']})
    return result


def isValidPassword(password1, password2):
    if password1 != password2:
        flash(gettext("Passwords do not match"), 'warning')
        return False
    if policy.test(password1):
        flash(gettext("Your password is weak"), 'warning')
        return False
    return True


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


def escapeMarkdown(MDtext):
    #return stripHTMLTags(MDtext)   # which expresion is best?
    return re.sub(r'<[^>]*?>', '', MDtext)


def markdown2HTML(MDtext):
    MDtext=escapeMarkdown(MDtext)
    return markdown.markdown(MDtext)


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


def isValidToken(data):
    token_age = datetime.datetime.now() - data['created']
    #print("token age: %s" % token_age)
    if token_age.total_seconds() < app.config['TOKEN_EXPIRATION']:
        return True
    return False
