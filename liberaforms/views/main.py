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

"""
def print_g(string=None):
    if string:
        print("printing from: %s" % string)
    for e in iter(g):
        print(e)
"""

@app.before_request
def before_request():
    g.site=None
    g.current_user=None
    g.isAdmin=False
    g.isRootUserEnabled=False
    g.embedded=False
    if request.path[0:7] == '/static':
        return
    g.site=Site.find(hostname=urlparse(request.host_url).hostname)
    if 'user_id' in session and session["user_id"] != None:
        g.current_user=User.find(id=session["user_id"], hostname=g.site.hostname)
        if not g.current_user:
            logout_user()
            return
        if g.current_user.isAdmin():
            g.isAdmin=True
        if not "root_enabled" in session:
            session["root_enabled"]=False
        if g.current_user.isRootUser() and session["root_enabled"] == True:
            g.isRootUserEnabled=True

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
