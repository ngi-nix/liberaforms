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
from flask_marshmallow import Marshmallow
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

from liberaforms.utils import setup
from liberaforms.config.config import config

db = SQLAlchemy()
ma = Marshmallow()
babel = Babel()
session = Session()
csrf = CSRFProtect()

#sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/form_templates")

def create_app():
    from liberaforms.config.logging import dictConfig

    app = Flask(__name__.split(".")[0])
    config_name = os.getenv('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    #print("LOG LEVEL: ", app.config['LOG_LEVEL'])
    #print("LOG TYPE: ", app.config['LOG_TYPE'])

    db.init_app(app)
    ma.init_app(app)
    babel.init_app(app)
    session.init_app(app)
    csrf.init_app(app)
    setup.ensure_uploads_dir_tree(app)

    if app.config["ENABLE_PROMETHEUS_METRICS"]:
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
        from liberaforms.metrics import initialize_metrics
        from prometheus_client import make_wsgi_app
        # Prometheus monitoring activation
        app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
            '/metrics': make_wsgi_app()
        })
        initialize_metrics(app)

    from liberaforms.commands import register_commands
    register_commands(app)
    register_blueprints(app)
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')

    app.logger.info("Created app")
    app.logger.debug("LOG LEVEL: %s", os.environ['LOG_LEVEL'])
    app.logger.debug("LOG TYPE: %s", os.environ['LOG_TYPE'])


    from liberaforms.utils.utils import populate_flask_g
    @app.before_request
    def before_request():
        if request.path[0:8] == '/static/':
            app.logger.warning('Serving a static file. Check Nginx config.')
        else:
            populate_flask_g()

    @app.after_request
    def after_request(response):
        """ Logging after every request. """
        logger = logging.getLogger("app.access")
        logger.info(
            "[%s] %s %s %s %s %s %s",
            datetime.utcnow().strftime("%d/%b/%Y:%H:%M:%S.%f")[:-3],
            request.method,
            request.path,
            request.scheme,
            response.status,
            response.content_length,
            request.referrer,
            #request.user_agent,
        )
        return response

    return app


def register_blueprints(app):
    from liberaforms.views.errors import errors_bp
    from liberaforms.views.main import main_bp
    from liberaforms.views.user import user_bp
    from liberaforms.views.media import media_bp
    from liberaforms.views.form import form_bp
    from liberaforms.views.site import site_bp
    from liberaforms.views.admin import admin_bp
    from liberaforms.views.answers import answers_bp
    from liberaforms.views.data_tables import data_table_bp
    from liberaforms.api.api import api_bp

    app.register_blueprint(errors_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(form_bp)
    app.register_blueprint(site_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(answers_bp)
    app.register_blueprint(data_table_bp)
    app.register_blueprint(api_bp)

    return None
