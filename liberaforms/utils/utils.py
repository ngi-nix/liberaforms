"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import json, string, random, datetime, uuid, pytz
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

def populate_flask_g():
    g.current_user=None
    g.is_admin=False
    g.embedded=False
    from urllib.parse import urlparse
    from liberaforms.models.site import Site
    from liberaforms.models.user import User
    g.site=Site.find(urlparse(request.host_url))
    g.timezone = pytz.timezone(current_app.config['DEFAULT_TIMEZONE'])
    if 'user_id' in session and session["user_id"] != None:
        g.current_user=User.find(id=session["user_id"])
        if not g.current_user:
            logout_user()
            return
        if g.current_user.is_admin():
            g.is_admin=True
        g.timezone = pytz.timezone(g.current_user.get_timezone())

def utc_to_g_timezone(utc_datetime):
    return utc_datetime.astimezone(g.timezone)

def get_app_version():
    try:
        with open('VERSION.txt') as f:
            app_version = f.readline().strip()
            return app_version if app_version else ""
    except Exception as error:
        current_app.logger.error(error)

"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    return Response(
        json_response,
        status_code,
        {'Content-Type':'application/json; charset=utf-8'}
    )

def return_error_as_json(status_code, sub_code, message, action):
    response = jsonify({
        'status': status_code,
        'sub_code': sub_code,
        'message': message,
        'action': action
    })
    return JsonResponse(response, status_code)


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

def human_readable_bytes(bytes):
    """ 1 KibiByte == 1024 Bytes
        1 Mebibyte == 1024*1024 Bytes
        1 GibiByte == 1024*1024*1024 Bytes
    """
    if bytes == 0:
        return "0 bytes"
    if bytes < 1024:
         return f"{bytes} bytes"
    if bytes < 1024*1024:
        return f"{float(round(bytes/(1024), 2))} KB"
    if bytes < 1024*1024*1024:
        return f"{float(round(bytes/(1024*1024), 2))} MB"
    return f"{float(round(bytes/(1024*1024*1024), 2))} GB"

def get_fuzzy_duration(start_time):
    now = datetime.datetime.now(datetime.timezone.utc)
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f%z")
    duration = now - start_time
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if days > 0:
        return _("{number} days".format(number = days))
    if hours > 0:
        return _("{number} hours".format(number = hours))
    if minutes > 0:
        return _("{number} minutes".format(number = minutes))
    return _("{number} seconds".format(number = seconds))
