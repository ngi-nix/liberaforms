"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import ast
import pytest
from urllib.parse import urlparse
from liberaforms.models.user import User

from tests.unit.conftest import test_user


class TestBootstrapAdmin():
    def test_bootstrap_first_admin(self, db, users, client):
        """ Creates the first admin user using ROOT_USER
            as defined in ./tests/test.env
        """
        root_user_email = ast.literal_eval(os.environ['ROOT_USERS'])[0]
        response = client.post(
                        "/site/recover-password",
                        data = {
                            "email": root_user_email,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 302
        # this path contains the invite token
        new_user_url = urlparse(response.location).path
        username = root_user_email.split('@')[0]
        password = users["admin_password"]
        response = client.post(
                            new_user_url,
                            data = {
                                "username": username,
                                "email": root_user_email,
                                "password": password,
                                "password2": password,
                            },
                            follow_redirects=True,
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- my_forms_page -->" in html
        assert '<a class="nav-link" href="/user/logout">' in html
        user = User.find(username=username)
        assert user.admin['isAdmin'] == True
        users['admin']=user

    def test_login(cls, users, admin_client):
        response = admin_client.get(
                        "/user/login",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form action="/user/login" method="POST"' in html
        response = admin_client.post(
                        "/user/login",
                        data = {
                            "username": users['admin'].username,
                            "password": users["admin_password"],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- my_forms_page -->" in html
        assert '<a class="nav-link" href="/user/logout">' in html