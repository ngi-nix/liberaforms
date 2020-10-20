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

import json, time, string, random, datetime, uuid
from pprint import pformat

from flask import Response, redirect, request, url_for
from flask import g, session #, has_app_context
from flask_babel import gettext

from liberaforms import app, babel


def print_obj_values(obj):
    values = {}
    fields = type(obj).__dict__['_fields']
    for key, _ in fields.items():
        value = getattr(obj, key, None)
        values[key] = value
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
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

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
    session["root_enabled"]=False
    g.current_user=None
    g.isAdmin=False
    g.isRootUserEnabled=False


"""
Create a unique token.
persistentClass may be a User class or an Invite class
"""
def createToken(persistentClass, **kwargs):
    tokenString = gen_random_string()
    while persistentClass.find(token=tokenString):
        tokenString = gen_random_string()
    result={'token': tokenString, 'created': datetime.datetime.now()}
    return {**result, **kwargs} 


""" ######## Dates ######## """

def isValidExpireDate(date):
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        return True
    except:
        return False

def isFutureDate(date):
    now=time.time()
    future=int(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%s"))
    return True if future > now else False


""" ######## Other ######## """

def gen_random_string():
    return uuid.uuid4().hex

def str2bool(v):
  return v.lower() in ("true", "1", "yes")
