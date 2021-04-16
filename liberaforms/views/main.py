"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from urllib.parse import urlparse
from flask import Blueprint, current_app
from flask import request, render_template, flash
from flask import g, session
from flask_wtf.csrf import CSRFError

from liberaforms.models.site import Site
from liberaforms.models.user import User
from liberaforms.utils.utils import logout_user

main_bp = Blueprint('main_bp',
                    __name__,
                    template_folder='../templates/main')

@main_bp.before_app_request
def before_request():
    g.current_user=None
    g.is_admin=False
    g.embedded=False
    if request.path[0:7] == '/static':
        # nginx should handle static files, but just in case.
        current_app.logger.warning('Serving a static file')
        return
    g.site=Site.find(urlparse(request.host_url))
    if 'user_id' in session and session["user_id"] != None:
        g.current_user=User.find(id=session["user_id"])
        if not g.current_user:
            logout_user()
            return
        if g.current_user.is_admin():
            g.is_admin=True


@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html', site=g.site)
