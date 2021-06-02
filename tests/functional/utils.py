"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

#import pytest

def login(client, user_creds):
    return client.post('/user/login', data=dict(
        username=user_creds['username'],
        password=user_creds['password']
    ), follow_redirects=True)

def logout(client):
    return client.post('/logout', follow_redirects=True)
