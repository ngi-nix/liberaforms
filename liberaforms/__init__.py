"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
#import sys
from flask import Flask #, session
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

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    babel.init_app(app)
    session.init_app(app)
    csrf.init_app(app)

    #from liberaforms.utils import database
    #database.create_tables()

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

    app.jinja_env.add_extension('jinja2.ext.loopcontrols')

    return app
