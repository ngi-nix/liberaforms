"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, logging
from datetime import datetime

#import sys
from flask import Flask, request
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

from liberaforms.config import config
from liberaforms.utils.logging import LogSetup

db = SQLAlchemy()
babel = Babel()
session = Session()
csrf = CSRFProtect()
logs = LogSetup()

#sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/form_templates")

def create_app():
    app = Flask(__name__.split(".")[0])
    config_name = os.getenv('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    logs.init_app(app)
    db.init_app(app)
    babel.init_app(app)
    session.init_app(app)
    csrf.init_app(app)

    from liberaforms.commands import register_commands
    register_commands(app)
    register_blueprints(app)

    @app.after_request
    def after_request(response):
        """ Logging after every request. """
        logger = logging.getLogger("app.access")
        logger.info(
            "[%s] %s %s %s %s %s %s %s",
            datetime.utcnow().strftime("%d/%b/%Y:%H:%M:%S.%f")[:-3],
            request.method,
            request.path,
            request.scheme,
            response.status,
            response.content_length,
            request.referrer,
            request.user_agent,
        )
        return response

    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    return app


def register_blueprints(app):
    from liberaforms.views.errors import errors_bp
    from liberaforms.views.main import main_bp
    from liberaforms.views.user import user_bp
    from liberaforms.views.form import form_bp
    from liberaforms.views.site import site_bp
    from liberaforms.views.admin import admin_bp
    from liberaforms.views.answers import answers_bp

    app.register_blueprint(errors_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(form_bp)
    app.register_blueprint(site_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(answers_bp)
    return None
