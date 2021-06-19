"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, ast
import logging

def get_SQLALCHEMY_DATABASE_URI():
    user = os.environ['DB_USER']
    pswd = os.environ['DB_PASSWORD']
    host = os.environ['DB_HOST']
    dbase = os.environ['DB_NAME']
    port = os.environ.get('DB_PORT', 5432)
    return f'postgresql+psycopg2://{user}:{pswd}@{host}:{port}/{dbase}'


class Config(object):
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    # WTF_CSRF_TIME_LIMIT. Time to fill out a form.
    # Must be less than PERMANENT_SESSION_LIFETIME
    WTF_CSRF_TIME_LIMIT = 21600
    # User sessions last 8h (refreshed on every request)
    PERMANENT_SESSION_LIFETIME = 28800
    RESERVED_SLUGS = [
        "static",
        "login", "logout",
        "admin", "admins", "root",
        "profile", "user", "users",
        "form", "forms",
        "site", "sites",
        "update",
        "embed",
        "api",
        "media", "file",
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
    FORMBUILDER_DISABLED_FIELDS = ["autocomplete", "hidden", "button"]
    FORMBUILDER_DISABLED_ATTRS = ["className", "toggle", "access", "multiple"]
    FORMBUILDER_CONTROL_ORDER = ["text", "textarea", "select", "radio-group",
                                 "checkbox-group", "date", "number", "file",
                                 "header", "paragraph"]
    BABEL_TRANSLATION_DIRECTORIES = "translations;form_templates/translations"
    # http://www.lingoes.net/en/translator/langcode.htm
    LANGUAGES = {
        "en": ("English", "en-US"),
        "ca": ("Català", "ca-ES"),
        "es": ("Castellano", "es-ES"),
        "eu": ("Euskara ", "eu-ES"),
    }
    #ROOT_USERS = ast.literal_eval(os.environ['ROOT_USERS'])
    TMP_DIR = os.environ['TMP_DIR']
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    DEFAULT_LANGUAGE = os.environ['DEFAULT_LANGUAGE']
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = get_SQLALCHEMY_DATABASE_URI()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = os.environ['SESSION_TYPE']
    TOKEN_EXPIRATION = os.environ['TOKEN_EXPIRATION']
    if SESSION_TYPE == "memcached":
        import pylibmc as memcache
        server = os.environ['MEMCACHED_HOST']
        SESSION_MEMCACHED = memcache.Client([server])
        if 'SESSION_KEY_PREFIX' in os.environ:
            SESSION_KEY_PREFIX = os.environ['SESSION_KEY_PREFIX']
        else:
            SESSION_KEY_PREFIX = "LF:"
    ENABLE_UPLOADS = True if os.environ['ENABLE_UPLOADS'] == 'True' else False
    ENABLE_REMOTE_STORAGE = True if os.environ['ENABLE_REMOTE_STORAGE'] == 'True' else False
    MAX_MEDIA_SIZE = int(os.environ['MAX_MEDIA_SIZE'])
    MAX_ATTACHMENT_SIZE = int(os.environ['MAX_ATTACHMENT_SIZE'])
    LOG_TYPE = os.environ['LOG_TYPE'] if 'LOG_TYPE' in os.environ else 'watched'
    LOG_DIR = os.environ['LOG_DIR']
    UPLOADS_DIR = os.path.join(ROOT_DIR, 'uploads')
    ATTACHMENT_DIR = 'attachments'
    MEDIA_DIR = 'media'
    BRAND_DIR = os.path.join(MEDIA_DIR, 'brand')
    if 'FQDN' in os.environ:
        # LiberaForms cluster project requires a unique directory
        LOG_DIR = os.path.join(LOG_DIR, "hosts", os.environ['FQDN'])
        ATTACHMENT_DIR = os.path.join(ATTACHMENT_DIR, "hosts", os.environ['FQDN'])
        MEDIA_DIR = os.path.join(MEDIA_DIR, "hosts", os.environ['FQDN'])
        BRAND_DIR = os.path.join(MEDIA_DIR, 'brand')

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.INFO


class StagingConfig(Config):
    DEVELOPMENT = True
    LOG_LEVEL = logging.INFO


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    LOG_LEVEL = logging.DEBUG
    LOG_TYPE = 'stream'


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = logging.DEBUG
    LOG_TYPE = 'stream'
    UPLOADS_DIR = os.path.join(Config.ROOT_DIR, 'tests', 'uploads')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
