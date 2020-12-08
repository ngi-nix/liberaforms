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

import os, shutil, uuid
from pathlib import Path

"""
Managed environment variables
"""
CONFIG_VARIABLES = [
    'SECRET_KEY',
    'FLASK_RUN_HOST',
    'FLASK_RUN_PORT',
    'SESSION_TYPE',
    'SESSION_KEY_PREFIX',
    'MEMCACHED_HOST',
    'MEMCACHED_PORT',
    'ROOT_USERS',
    'MONGODB_DB',
    'MONGODB_HOST',
    'MONGODB_PORT',
    'MONGODB_USERNAME',
    'MONGODB_PASSWORD'
]

def load_app_config(app):
    # Load config defaults
    app.config.from_object(DefaultConfig)
    # User overrides. Future: This should only be done if not running from docker
    app.config.from_pyfile('config.cfg', silent=True)
    # Force internal configuration
    app.config.from_object(InternalConfig)
    # Merge extra configuration as/if necessary
    for cfg_item in ["RESERVED_SLUGS", "RESERVED_USERNAMES"]:
        app.config[cfg_item].extend(app.config["EXTRA_{}".format(cfg_item)])
    app.config["APP_VERSION"] = open(os.path.join(app.root_path, 'VERSION')).read().rstrip()
    app.secret_key = app.config["SECRET_KEY"]



class DefaultConfig(object):
    # Required config:
    # SECRET_KEY = 'super secret key'
    # ROOT_USERS = ['your_email_address@example.com']
    # MONGODB_HOST = '127.0.0.1'
    # MONGODB_PORT = 27017
    # MONGODB_DB = 'liberaforms'

    """
    User overridable settings with their sensible defaults.
    """
    
    # Optional config:
    DEFAULT_LANGUAGE = "en"
    TMP_DIR = "/tmp"

    # Session management (see docs/INSTALL)
    SESSION_TYPE = "filesystem"
    #SESSION_TYPE = "memcached"
    
    # Should be passed as an env variable with docker
    SESSION_KEY_PREFIX = 'liberaforms'

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
    Internal settings that cannot be overridden.
    """

    SCHEMA_VERSION = 24

    RESERVED_SLUGS = [
        "login",
        "logout",
        "admin", "admins",
        "user", "users",
        "form", "forms",
        "site", "sites",
        "profile",
        "update",
        "embed",
        "api",
        "static",
        "upload", "uploads",
        "logo", "favicon.ico",
    ]
    # DPL = Data Protection Law
    RESERVED_FORM_ELEMENT_NAMES = [
        "marked",
        "created",
        "csrf_token",
        "DPL",
        "id",
        "checked",
        "sendConfirmation"
    ]
    RESERVED_USERNAMES = ["system", "admin", "root"]
    
    #CONDITIONAL_FIELD_TYPES = ['select']

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

def ensure_app_config(app):
    conf_path = os.path.join(app.instance_path, 'config.cfg')
    if not os.path.isfile(conf_path):
        os.makedirs(app.instance_path, exist_ok=True)
        example_cfg = os.path.join(app.root_path, 'config.example.cfg')
        shutil.copyfile(example_cfg, conf_path)

# Maybe shouldn't do this when running as a container.
def ensure_branding_dir(app):
    branding_dir = os.path.join(app.instance_path, 'branding')
    if not os.path.isdir(branding_dir):
        os.makedirs(branding_dir, exist_ok=True)

def load_env_variables(app):
    for variable in CONFIG_VARIABLES:
        if variable in os.environ:
            app.config[variable] = os.environ[variable]

def setup_session_type(app):
    app.session_type = app.config["SESSION_TYPE"]
    if app.config["SESSION_TYPE"] == "filesystem":
        app.config["SESSION_FILE_DIR"] = os.path.join(app.instance_path, 'sessions')
        return
    if app.config['SESSION_TYPE'] == "memcached":
        if 'MEMCACHED_HOST' in app.config:
            import pylibmc
            if 'MEMCACHED_PORT' in app.config:
                _server = "{}:{}".format(   app.config['MEMCACHED_HOST'],
                                            app.config['MEMCACHED_PORT'])
            else:
                _server = "{}:11211".format(app.config['MEMCACHED_HOST'])
            app.config['SESSION_MEMCACHED'] = pylibmc.Client([_server])
