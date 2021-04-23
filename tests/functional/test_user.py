"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest


#@pytest.mark.usefixtures('saved_user')
class TestUser():
    def test_saved_user(self, saved_user):
        assert saved_user.id != None

    def test_bad_login(self, client):
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

    def test_login(self, client, saved_user):
        response = client.post(
                        "/user/login",
                        data = {
                            "username": saved_user.username,
                            "password": os.environ['TEST_USER_PASSWORD'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_logout(self, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/login">' in html
