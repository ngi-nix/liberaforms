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
    if not 'CRYPTO_KEY' in os.environ:
        current_app.logger.error("CRYPTO_KEY not found in .env")
        return None
    fernet = Fernet(os.environ['CRYPTO_KEY'])
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
    if not 'CRYPTO_KEY' in os.environ:
        current_app.logger.error("CRYPTO_KEY not found in .env")
        return None
    fernet = Fernet(os.environ['CRYPTO_KEY'])
    try:
        return fernet.decrypt(encrypted_file_content)
    except Exception as error:
        current_app.logger.error(error)
        return None
