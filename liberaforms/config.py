"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, shutil
import logging

def get_SQLALCHEMY_DATABASE_URI():
    user = os.environ['DB_USER']
    pswd = os.environ['DB_PASSWORD']
    host = os.environ['DB_HOST']
    dbase = os.environ['DB_NAME']
    port = os.environ.get('DB_PORT', 5432)
    uri = f'postgresql+psycopg2://{user}:{pswd}@{host}:{port}/{dbase}'
    return uri


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    # WTF_CSRF_TIME_LIMIT. Time to fill out a form.
    # Must be less than PERMANENT_SESSION_LIFETIME
    WTF_CSRF_TIME_LIMIT = 21600
    # User sessions last 8h (refreshed on every request)
    PERMANENT_SESSION_LIFETIME = 28800
    RESERVED_SLUGS = [
        "login",
        "logout",
        "static",
        "admin",
        "admins",
        "user",
        "users",
        "profile",
        "root",
        "form",
        "forms",
        "site",
        "sites",
        "update",
        "embed",
        "api"
    ]
    # DPL = Data Protection Law
    RESERVED_FORM_ELEMENT_NAMES = [
        "marked",
        "created",
        "form_id"
        "csrf_token",
        "DPL",
        "id",
        "checked",
        "sendConfirmation"
    ]
    RESERVED_USERNAMES = ["system", "admin", "root"]
    FORMBUILDER_DISABLED_ATTRS = ["className", "toggle", "access"]
    FORMBUILDER_DISABLE_FIELDS = ["autocomplete", "hidden", "button", "file"]
    FORMBUILDER_CONTROL_ORDER = ["header", "paragraph"]
    BABEL_TRANSLATION_DIRECTORIES = "translations;form_templates/translations"
    # http://www.lingoes.net/en/translator/langcode.htm
    LANGUAGES = {
        "en": ("English", "en-US"),
        "ca": ("Català", "ca-ES"),
        "es": ("Castellano", "es-ES"),
        "eu": ("Euskara ", "eu-ES"),
    }
    DEFAULT_LANGUAGE = os.environ['DEFAULT_LANGUAGE']
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = get_SQLALCHEMY_DATABASE_URI()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = os.environ['SESSION_TYPE']
    if SESSION_TYPE == "memcached":
        import pylibmc as memcache
        server = os.environ['MEMCACHED_HOST']
        SESSION_MEMCACHED = memcache.Client([server])
        SESSION_KEY_PREFIX = os.environ['SESSION_KEY_PREFIX'] or "LF:"
    LOGGING_TYPE = os.environ['LOGGING_TYPE']
    LOGGING_FORMAT = '%(asctime)s: %(name)s:%(levelname)s: %(message)s'
    if LOGGING_TYPE == "filesystem":
        LOGGING_LOCATION = os.environ['LOGGING_LOCATION']
    TOKEN_EXPIRATION = os.environ['TOKEN_EXPIRATION']

    base_dir = os.path.dirname(os.path.abspath(__file__))
    instancefiles = 'instancefiles'
    BRAND_DIR = os.path.join(base_dir, instancefiles, 'brand')
    if 'FQDN' in os.environ:
        # LiberaForms' cluster project requires a unique directory
        brand_dir = os.path.join(   base_dir,
                                    instancefiles,
                                    "hosts",
                                    os.environ['FQDN'],
                                    "brand")
        if not os.path.isdir(brand_dir):
            #os.mkdir(host_brand_dir)
            shutil.copytree(BRAND_DIR, brand_dir)
        BRAND_DIR = brand_dir


    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    DEBUG = False
    LOGGING_LEVEL = logging.WARNING


class StagingConfig(Config):
    DEVELOPMENT = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    LOGGING_LEVEL = logging.DEBUG


class TestingConfig(Config):
    TESTING = True
    LOGGING_LEVEL = logging.DEBUG


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
