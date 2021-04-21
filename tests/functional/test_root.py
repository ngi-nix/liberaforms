"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os


def test_landing(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode()
    assert '<div id="blurb" class="marked-up">' in html

"""
def test_login(client):
    response = client.post(
                    "/user/login",
                    data = {
                        "username": os.environ['TEST_USERNAME'],
                        "password": os.environ['TEST_USER_PASSWORD'],
                    },
                    follow_redirects=True,
                )
    assert response.status_code == 200
    html = response.data.decode()
    assert '<a class="nav-link" href="/user/logout">' in html
"""

def test_bad_login(client):
    response = client.post(
                    "/user/login",
                    data = {
                        "username": os.environ['TEST_USERNAME'],
                        "password": os.environ['TEST_USER_PASSWORD']+'*',
                    },
                    follow_redirects=True,
                )
    assert response.status_code == 200
    html = response.data.decode()
    assert '<form action="/user/login"' in html

"""
def test_logout(client):
    response = client.post(
                    "/user/logout",
                    follow_redirects=True,
                )
    assert response.status_code == 200
    html = response.data.decode()
    assert '<a class="nav-link" href="/user/login">' in html
"""
