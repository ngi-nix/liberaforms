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
from flask import flash
from formbuilder import app
from unidecode import unidecode
import re, string, random
import csv
from passlib.hash import pbkdf2_sha256
from password_strength import PasswordPolicy
from validate_email import validate_email

policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=0,  # need min. 2 uppercase letters
    numbers=0,  # need min. 2 digits
    special=0,  # need min. 2 special characters
    nonletters=1,  # need min. 2 non-letter characters (digits, specials, anything)
)

"""
passwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    salt_size=16,
    pbkdf2_sha256__default_rounds=200000
)
"""

def sanitizeSlug(slug):
    if slug in app.config['RESERVED_SLUGS']:
        return None
    slug = slug.lower()
    slug = slug.replace(" ", "-") 
    return sanitizeString(slug)


def sanitizeString(string):
    string = unidecode(string)
    string = string.replace(" ", "") 
    return re.sub('[^A-Za-z0-9\-]', '', string)


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


def isValidPassword(password1, password2):
    if password1 != password2:
        flash("Passwords do not match", 'warning')
        return False
    if policy.test(password1):
        flash("Your password is weak", 'warning')
        return False
    return True


def isValidEmail(email):
    if not validate_email(email):
        flash("Email address is not valid", 'warning')
        return False
    return True


def writeCSV(form):
    fieldnames=[]
    fieldheaders={}
    for field in form.fieldIndex:
        fieldnames.append(field['name'])
        fieldheaders[field['name']]=field['label']
      
    csv_name='/tmp/%s.csv' % form.slug
    
    with open(csv_name, mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writerow(fieldheaders)
        for entry in form.data['entries']:
            writer.writerow(entry)

    return csv_name
