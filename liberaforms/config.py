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

import os


class DefaultConfig(object):
    """
    User overridable settings with their sensible defaults.
    """
    # Required config:
    # SECRET_KEY = 'super secret key'
    # ROOT_USERS = ['your_email_address@example.com']
    ## MongoDB config
    # MONGODB_SETTINGS = {'host': 'mongodb://localhost:27017/LiberaForms'}

    # Optional config:
    DEFAULT_LANGUAGE = "en"
    TMP_DIR = "/tmp"
    
    # 3600 seconds = 1hrs. Time to fill out a form.
    # This number must be less than PERMANENT_SESSION_LIFETIME (see below)
    WTF_CSRF_TIME_LIMIT = 21600
    
    # User sessions last 8h (refreshed on every request)
    PERMANENT_SESSION_LIFETIME = 28800
    
    # 86400 seconds = 24h ( token are used for password resets, invitations, ..)
    TOKEN_EXPIRATION = 604800
    
    # formbuilder
    FORMBUILDER_CONTROL_ORDER = ["header", "paragraph"]

    # Extra configuration to be merged with standard config
    EXTRA_RESERVED_SLUGS = []
    EXTRA_RESERVED_USERNAMES = []


class InternalConfig(object):
    """
    Internal settings that CANNOT be overridden.
    """

    APP_VERSION = "1.8.5"
    SCHEMA_VERSION = 24

    RESERVED_SLUGS = [
        "login",
        "static",
        "admin",
        "admins",
        "user",
        "users",
        "form",
        "forms",
        "site",
        "sites",
        "update",
        "embed"
    ]
    # DPL = Data Protection Law
    RESERVED_FORM_ELEMENT_NAMES = [
        "created",
        "csrf_token",
        "DPL",
        "id",
        "checked",
        "sendConfirmation"
    ]
    RESERVED_USERNAMES = ["system", "admin"]
    
    CONDITIONAL_FIELD_TYPES = ['select']

    FORMBUILDER_DISABLED_ATTRS = ["className", "toggle", "access"]
    FORMBUILDER_DISABLE_FIELDS = ["autocomplete", "hidden", "button", "file"]

    BABEL_TRANSLATION_DIRECTORIES = "translations;form_templates/translations"
    # http://www.lingoes.net/en/translator/langcode.htm
    LANGUAGES = {
        "en": ("English", "en-US"),
        "ca": ("Català", "ca-ES"),
        "es": ("Castellano", "es-ES"),
        "eu": ("Euskara ", "eu-ES"),
    }    
    FAVICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "static/images/favicon/")
