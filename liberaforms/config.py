"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = 21600
    PERMANENT_SESSION_LIFETIME = 28800
    EXTRA_RESERVED_SLUGS = []
    EXTRA_RESERVED_USERNAMES = []
    FORMBUILDER_CONTROL_ORDER = ["header", "paragraph"]
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

    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    SESSION_TYPE = os.environ['SESSION_TYPE']
    TOKEN_EXPIRATION = os.environ['TOKEN_EXPIRATION']

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True


class TestingConfig(Config):
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
