"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import pytest
from urllib.parse import urlparse
from liberaforms.models.user import User


class TestBootstrapAdmin():
    def test_bootstrap_first_admin(self, db, users, client):
        """ Creates the first admin user using ROOT_USER
            as defined in ./tests/test.env
        """
        response = client.post(
                        "/site/recover-password",
                        data = {
                            "email": users['admin']['email'],
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 302
        # this path contains the invite token
        new_user_url = urlparse(response.location).path
        response = client.post(
                            new_user_url,
                            data = {
                                "username": users['admin']['username'],
                                "email": users['admin']['email'],
                                "password": users['admin']['password'],
                                "password2": users['admin']['password'],
                            },
                            follow_redirects=True,
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- user_settings_page -->" in html
        assert '<a class="nav-link" href="/user/logout">' in html
        user = User.find(username=users['admin']['username'])
        assert user.admin['isAdmin'] == True

    def test_login(cls, users, client):
        response = client.get(
                        "/user/login",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form action="/user/login" method="POST"' in html
        response = client.post(
                        "/user/login",
                        data = {
                            "username": users['admin']['username'],
                            "password": users['admin']['password'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- list_templates_page -->" in html
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_logout(self, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        assert '<a class="nav-link" href="/user/login">' in html
