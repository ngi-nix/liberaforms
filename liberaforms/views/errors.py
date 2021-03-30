"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask_wtf.csrf import CSRFError
from flask import Blueprint, render_template
from flask import flash

errors_bp = Blueprint('errors_bp',
                      __name__,
                      template_folder='../templates/errors')

@errors_bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('page-not-found.html', error=error), 400

@errors_bp.app_errorhandler(500)
def server_error(error):
    return render_template('server-error.html', error=error), 500

@errors_bp.app_errorhandler(CSRFError)
def handle_csrf_error(e):
    flash(e.description, 'error')
    return render_template('server-error.html', error=e.description), 500
