"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import json, string, random, datetime, uuid
from pprint import pformat

from flask import Response, redirect, request, url_for
from flask import current_app, g, session
from flask_babel import gettext as _

from liberaforms import babel


def print_obj_values(obj):
    values={}
    obj_vars = vars(obj)
    for var in obj_vars:
        values[var] = obj_vars[var]
    return pformat({obj.__class__.__name__: values})

def make_url_for(function, **kwargs):
    kwargs["_external"]=True
    if 'site' in g:
        kwargs["_scheme"]=g.site.scheme
    return url_for(function, **kwargs)

@babel.localeselector
def get_locale():
    if 'current_user' in g and g.current_user:
        return g.current_user.language
    else:
        return request.accept_languages.best_match(
                                        current_app.config['LANGUAGES'].keys()
                                        )

"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    return Response(
        json_response,
        status_code,
        {'Content-Type':'application/json; charset=utf-8'}
    )


""" ######## Session ######## """
def logout_user():
    if "user_id" in session:
        session.pop("user_id")
    g.current_user=None
    g.is_admin=False


"""
Create a unique token.
persistentClass may be a User class or an Invite class
"""
def create_token(persistentClass, **kwargs):
    token_string = gen_random_string()
    while persistentClass.find(token=token_string):
        token_string = gen_random_string()
    created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result={'token': token_string, 'created': created}
    return {**result, **kwargs}

""" ######## Other ######## """

def gen_random_string():
    return uuid.uuid4().hex

def str2bool(v):
  return v.lower() in ("true", "1", "yes")
