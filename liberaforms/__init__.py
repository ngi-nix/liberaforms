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

import sys, os, uuid 
from flask import Flask, session
from flask_session import Session
from flask_mongoengine import MongoEngine
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

#from liberaforms.utils import utils
from liberaforms import config

app = Flask(__name__, instance_relative_config=True)

app.config["APP_VERSION"] = open(os.path.join(app.root_path, 'VERSION')).read().rstrip()

# Load config defaults
app.config.from_object(config.DefaultConfig)
# Ensure instance dir and content are in place
config.default_instance_setup(app)
# User overrides
app.config.from_pyfile('config.cfg', silent=True)
# Force internal configuration
app.config.from_object(config.InternalConfig)
# Merge extra configuration as/if necessary
for cfg_item in ["RESERVED_SLUGS", "RESERVED_USERNAMES"]:
    app.config[cfg_item].extend(app.config["EXTRA_{}".format(cfg_item)])
config.load_env_variables(app, os.environ)

db = MongoEngine(app)
babel = Babel(app)

app.secret_key = app.config["SECRET_KEY"]
app.session_type = app.config["SESSION_TYPE"]
if app.config["SESSION_TYPE"] == "filesystem":
    app.config["SESSION_FILE_DIR"] = os.path.join(app.instance_path, 'sessions')
app.config['SESSION_KEY_PREFIX'] = str(uuid.uuid1())
Session(app)

csrf = CSRFProtect()
csrf.init_app(app)

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/form_templates")

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
