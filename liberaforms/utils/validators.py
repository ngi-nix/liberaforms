"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
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

import re, datetime, time, uuid
from liberaforms import app
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
    return pbkdf2_sha256.hash(password, rounds=200000, salt_size=16)

def verify_password(password, hash):
    return pbkdf2_sha256.verify(password, hash)

def is_valid_token(tokenData):
    token_age = datetime.datetime.now() - tokenData['created']
    if token_age.total_seconds() > app.config['TOKEN_EXPIRATION']:
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
