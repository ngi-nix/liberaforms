"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

#import pytest
from flask import g

def login(client, user_creds):
    response = client.post('/user/login', data=dict(
        username=user_creds['username'],
        password=user_creds['password']
    ), follow_redirects=True)
    assert g.current_user.username == user_creds['username']
    return response

def logout(client):
    initial_current_user = g.current_user
    response = client.post('/user/logout', follow_redirects=True)
    assert g.current_user == None
    return response
