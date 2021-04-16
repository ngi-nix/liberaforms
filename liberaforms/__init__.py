"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, logging
#import sys
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

from liberaforms.config import config

db = SQLAlchemy()
babel = Babel()
session = Session()
csrf = CSRFProtect()

#sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/form_templates")

def create_app():
    app = Flask(__name__)
    config_name = os.getenv('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    babel.init_app(app)
    session.init_app(app)
    csrf.init_app(app)

    # Configure logging
    if app.config['LOGGING_TYPE'] == "filesystem":
        handler = logging.FileHandler(app.config['LOGGING_LOCATION'])
        handler.setLevel(app.config['LOGGING_LEVEL'])
        formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

    register_blueprints(app)

    from liberaforms.commands import register_commands
    register_commands(app)

    app.jinja_env.add_extension('jinja2.ext.loopcontrols')

    return app


def register_blueprints(app):
    from liberaforms.views.errors import errors_bp
    from liberaforms.views.main import main_bp
    from liberaforms.views.user import user_bp
    from liberaforms.views.form import form_bp
    from liberaforms.views.site import site_bp
    from liberaforms.views.admin import admin_bp
    from liberaforms.views.entries import entries_bp

    app.register_blueprint(errors_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(form_bp)
    app.register_blueprint(site_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(entries_bp)
