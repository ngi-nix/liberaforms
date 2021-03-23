"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from urllib.parse import urlparse
from flask import request, render_template, redirect, flash
from flask import g, session, Blueprint
from flask_wtf.csrf import CSRFError

#from flask import current_app
#from flask import ctx, current_app, has_app_context, app_ctx_globals_class

from liberaforms import app
from liberaforms.models.site import Site
from liberaforms.models.user import User
from liberaforms.utils.utils import logout_user
from liberaforms.utils.wraps import *


main_bp = Blueprint('main_bp', __name__,
                    template_folder='../templates/main')
#main_bp.before_request(shared_functions.before_request)

@app.before_request
def before_request():
    g.current_user=None
    g.is_admin=False
    g.embedded=False
    if request.path[0:7] == '/static':
        return
    g.site=Site.find(urlparse(request.host_url))
    if 'user_id' in session and session["user_id"] != None:
        g.current_user=User.find(id=session["user_id"])
        if not g.current_user:
            logout_user()
            return
        if g.current_user.is_admin():
            g.is_admin=True

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page-not-found.html', error=error), 400

@app.errorhandler(500)
def server_error(error):
    return render_template('server-error.html', error=error), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash(e.description, 'error')
    return render_template('server-error.html', error=e.description), 500

@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html', site=g.site)


"""
@enabled_user_required
@main_bp.route('/test', methods=['GET'])
def test():
    return render_template('test.html', sites=[])
"""
