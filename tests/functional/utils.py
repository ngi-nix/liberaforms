"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

#import pytest
from flask import g
from pprint import pprint

def login(client, user_creds):
    response = client.post('/user/login', data=dict(
        username=user_creds['username'],
        password=user_creds['password']
    ), follow_redirects=True)
    return response

def logout(client):
    username = g.current_user.username if g.current_user else None
    response = client.post('/user/logout', follow_redirects=True)
    assert g.current_user == None
    return response
