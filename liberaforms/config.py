"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, shutil, ast
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
    WTF_CSRF_ENABLED = True
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
        "api",
        "file"
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
    FORMBUILDER_DISABLED_FIELDS = ["autocomplete", "hidden", "button"]
    FORMBUILDER_CONTROL_ORDER = ["header", "paragraph"]
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
        SESSION_KEY_PREFIX = os.environ['SESSION_KEY_PREFIX'] or "LF:"
    ENABLE_UPLOADS = True if os.environ['ENABLE_UPLOADS'] == 'True' else False
    MAX_FILE_UPLOAD_SIZE = os.environ['MAX_FILE_UPLOAD_SIZE']
    LOG_TYPE = os.environ['LOG_TYPE']
    LOG_DIR = os.environ['LOG_DIR']

    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
    root_dir = os.path.abspath(root_dir)
    instancefiles = 'instancefiles'
    BRAND_DIR = os.path.join(root_dir, instancefiles, 'brand')
    UPLOAD_DIR = os.path.join(root_dir, instancefiles, 'uploads')
    if 'FQDN' in os.environ:
        # LiberaForms cluster project requires a unique directory
        fqdn_brand_dir = os.path.join(BRAND_DIR, "hosts", os.environ['FQDN'])
        if not os.path.isdir(fqdn_brand_dir):
            shutil.copytree(BRAND_DIR, fqdn_brand_dir)
        BRAND_DIR = fqdn_brand_dir
        fqdn_uploads_dir = os.path.join(UPLOAD_DIR, "hosts", os.environ['FQDN'])
        if not os.path.isdir(fqdn_uploads_dir):
            shutil.copytree(UPLOAD_DIR, fqdn_uploads_dir)
        UPLOAD_DIR = fqdn_uploads_dir
    if os.environ['ENABLE_REMOTE_STORAGE'] == 'True':
        ENABLE_REMOTE_STORAGE = True
    else:
        ENABLE_REMOTE_STORAGE = False
    MINIO_HOST = os.environ['MINIO_HOST']
    MINIO_ACCESS_KEY = os.environ['MINIO_ACCESS_KEY']
    MINIO_SECRET_KEY = os.environ['MINIO_SECRET_KEY']

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.WARNING


class StagingConfig(Config):
    DEVELOPMENT = True
    LOG_LEVEL = logging.WARNING


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    LOG_LEVEL = logging.DEBUG


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = logging.DEBUG


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
