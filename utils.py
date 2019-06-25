from formbuilder import app, mongo
from flask import flash
from formbuilder import app
from unidecode import unidecode
import re, string, random
from passlib.hash import pbkdf2_sha256
#from passlib.context import CryptContext
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
    slug = unidecode(slug)
    slug = slug.lower()
    slug = slug.replace(" ", "-")
    return re.sub('[^A-Za-z0-9\-]', '', slug)
    
    p = re.compile(r"(\b[-']\b)|[\W_]")
    return p.sub(lambda m: (m.group(1) if m.group(1) else " "), slug)


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
    """
    l = list(filter(lambda field: field['name'] == name, index))
    if l:
        return l[0]
    return None
    """

def isValidPassword(password1, password2):
    if password1 != password2:
        flash("Passwords do not match", 'info')
        return False
    if policy.test(password1):
        flash("Your password is weak", 'info')
        return False
    return True


def isValidEmail(email):
    if not validate_email(email):
        flash("email address is not valid", 'info')
        return False
    return True
