"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import traceback
from flask_wtf.csrf import CSRFError
from flask import Blueprint, render_template, request
from flask import current_app, flash
from liberaforms.utils.dispatcher import Dispatcher

errors_bp = Blueprint('errors_bp',
                      __name__,
                      template_folder='../templates/errors')

@errors_bp.app_errorhandler(404)
def page_not_found(error):
    current_app.logger.error(f'Page not found: {request.path}')
    return render_template('page-not-found.html', error=error), 400

@errors_bp.app_errorhandler(500)
def server_error(error):
    Dispatcher().send_error(traceback.format_exc())
    current_app.logger.error(f'Server Error: {error}')
    return render_template('server-error.html', error=error), 500

@errors_bp.app_errorhandler(CSRFError)
def handle_csrf_error(error):
    current_app.logger.warning(f'Server Error: {error}')
    flash(error.description, 'error')
    return render_template('server-error.html', error=error.description), 500
