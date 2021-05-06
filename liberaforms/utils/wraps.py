"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from functools import wraps
from flask import current_app, g
from flask import redirect, url_for, render_template, flash
from flask_babel import gettext as _
from liberaforms.utils import sanitizers
from liberaforms.utils import validators


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('main_bp.index'))
    return wrap

def enabled_user_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user and g.current_user.enabled:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('main_bp.index'))
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.is_admin:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('main_bp.index'))
    return wrap

def rootuser_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user and g.current_user.is_root_user():
            return f(*args, **kwargs)
        else:
            return redirect(url_for('main_bp.index'))
    return wrap

def anon_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user:
            return redirect(url_for('main_bp.index'))
        else:
            return f(*args, **kwargs)
    return wrap

"""
def queriedForm_editor_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        queriedForm=models.Form.find(id=kwargs['id'], editor_id=str(g.current_user.id))
        if not queriedForm:
            flash(_("Form is not available. 404"), 'warning')
            return redirect(make_url_for('forms_bp.my_forms'))
        kwargs['queriedForm']=queriedForm
        return f(*args, **kwargs)
    return wrap
"""

def sanitized_slug_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not 'slug' in kwargs:
            if g.current_user:
                flash("No slug found!", 'error')
            return render_template('page-not-found.html'), 404
        if kwargs['slug'] in current_app.config['RESERVED_SLUGS']:
            if g.current_user:
                flash("Reserved slug!", 'warning')
            return render_template('page-not-found.html'), 404
        if kwargs['slug'] != sanitizers.sanitize_slug(kwargs['slug']):
            if g.current_user:
                flash("That's a nasty slug!", 'warning')
            return render_template('page-not-found.html'), 404
        return f(*args, **kwargs)
    return wrap

def sanitized_key_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not ('key' in kwargs and kwargs['key'] == sanitizers.sanitize_string(kwargs['key'])):
            if g.current_user:
                flash(_("That's a nasty key!"), 'warning')
            return render_template('page-not-found.html'), 404
        else:
            return f(*args, **kwargs)
    return wrap

def sanitized_token(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'token' in kwargs and not validators.is_valid_UUID(kwargs['token']):
            if g.current_user:
                flash(_("That's a nasty token!"), 'warning')
            return render_template('page-not-found.html'), 404
        else:
            return f(*args, **kwargs)
    return wrap
