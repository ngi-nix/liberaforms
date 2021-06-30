"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, current_app
from flask import request, render_template#, flash
from flask import g #, session
#from flask_wtf.csrf import CSRFError

main_bp = Blueprint('main_bp',
                    __name__,
                    template_folder='../templates/main')


@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html', site=g.site)
