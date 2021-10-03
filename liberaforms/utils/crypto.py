"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
from flask import current_app
from cryptography.fernet import Fernet


def encrypt_file(file_path):
    """ Returns the path of the encrypted file """
    if not current_app.config['CRYPTO_KEY']:
        current_app.logger.warning("CRYPTO_KEY not found in .env")
        return None
    fernet = Fernet(current_app.config['CRYPTO_KEY'])
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            original_path = f.name
        encrypted_content = fernet.encrypt(content)
        encrypted_file_path = f"{original_path}.enc"
        with open(encrypted_file_path, mode='wb') as encrypted_file:
            encrypted_file.write(encrypted_content)
        return encrypted_file_path
    except Exception as error:
        current_app.logger.error(error)
        return None

def decrypt_file_content(encrypted_file_content):
    if not current_app.config['CRYPTO_KEY']:
        current_app.logger.warning("CRYPTO_KEY not found in .env")
        return None
    fernet = Fernet(current_app.config['CRYPTO_KEY'])
    try:
        return fernet.decrypt(encrypted_file_content)
    except Exception as error:
        current_app.logger.error(error)
        return None


""" Encrypt a dict {key: string}
    Returns a dict {key: encrypted_string}
"""
def encrypt_dict(dictionary):
    if not current_app.config['CRYPTO_KEY']:
        current_app.logger.warning("CRYPTO_KEY not found in .env")
        return None
    fernet = Fernet(current_app.config['CRYPTO_KEY'])
    result = {}
    try:
        for key, value in dictionary.items():
            result[key] = fernet.encrypt(value.encode()).decode()
        return result
    except Exception as error:
        current_app.logger.error(error)
        return None

def decrypt_dict(enc_dictionary):
    if not current_app.config['CRYPTO_KEY']:
        current_app.logger.warning("CRYPTO_KEY not found in .env")
        return None
    fernet = Fernet(current_app.config['CRYPTO_KEY'])
    result = {}
    try:
        for key, value in enc_dictionary.items():
            result[key] = fernet.decrypt(value.encode()).decode()
        return result
    except Exception as error:
        current_app.logger.error(error)
        return None
