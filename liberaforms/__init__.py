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

from flask import Flask, session
from flask_session import Session
from flask_mongoengine import MongoEngine
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

from liberaforms import config

app = Flask(__name__, instance_relative_config=True)

config.ensure_app_config(app)
config.ensure_branding_dir(app)
config.load_app_config(app)
config.load_env_variables(app)
config.setup_session_type(app)

db = MongoEngine(app)
babel = Babel(app)
Session(app)

csrf = CSRFProtect()
csrf.init_app(app)

#sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/form_templates")

from liberaforms.views.main import main_bp
from liberaforms.views.user import user_bp
from liberaforms.views.form import form_bp
from liberaforms.views.site import site_bp
from liberaforms.views.admin import admin_bp
from liberaforms.views.entries import entries_bp

app.register_blueprint(main_bp)
app.register_blueprint(user_bp)
app.register_blueprint(form_bp)
app.register_blueprint(site_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(entries_bp)

import liberaforms.cli.custom_commands

app.jinja_env.add_extension('jinja2.ext.loopcontrols')
