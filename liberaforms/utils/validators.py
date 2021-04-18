"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import re, datetime, time, uuid
from validate_email import validate_email
from passlib.hash import pbkdf2_sha256
from password_strength import PasswordPolicy


def is_valid_email(email):
    return validate_email(email)

pwd_policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=0,  # need min. 2 uppercase letters
    numbers=0,  # need min. 2 digits
    special=0,  # need min. 2 special characters
    nonletters=1,  # need min. 2 non-letter characters (digits, specials, anything)
)

def hash_password(password):
    settings = {
        'rounds': 200000,
        'salt_size': 16,
    }
    return pbkdf2_sha256.using(**settings).hash(password)

def verify_password(password, hash):
    return pbkdf2_sha256.verify(password, hash)

def has_token_expired(token_data):
    token_created = datetime.datetime.strptime( token_data['created'],
                                                "%Y-%m-%d %H:%M:%S")
    token_age = datetime.datetime.now() - token_created
    if token_age.total_seconds() <= int(os.environ['TOKEN_EXPIRATION']):
        return False
    return True

def is_hex_color(color):
    return bool(re.search("^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", color))

def is_valid_UUID(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def is_valid_date(date):
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        return True
    except:
        return False

def is_future_date(date):
    now=time.time()
    future=int(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%s"))
    return True if future > now else False
