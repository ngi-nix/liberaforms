"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask import current_app
from liberaforms.models.user import User


class TestNewUser():
    def test_new_user_form(self, client, site, users):
        """ Tests new user form
            Tests site.invitationOnly
            Tests RESERVED_USERNAMES
            Tests invalid email and passwords
        """
        url = "/user/new"
        site.invitationOnly = True
        site.save()
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        site.invitationOnly = False
        site.save()
        response = client.get(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- new_user_form_page -->' in html
        assert '<a class="nav-link" href="/user/login">' in html
        reserved_username = current_app.config['RESERVED_USERNAMES'][0]
        response = client.post(
                        url,
                        data = {
                            "username": reserved_username,
                            "email": "invalid_email_string",
                            "password": "invalidpassword",
                            "password2": "valid password",
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- new_user_form_page -->' in html
        assert '<a class="nav-link" href="/user/login">' in html
        assert html.count('<span class="formError">') == 4

    def test_create_user_account(self, client, users):
        url = "/user/new"
        response = client.post(
                        url,
                        data = {
                            "username": os.environ['TEST_USERNAME'],
                            "email": os.environ['TEST_USER_EMAIL'],
                            "password": os.environ['TEST_USER_PASSWORD'],
                            "password2": os.environ['TEST_USER_PASSWORD'],
                            "termsAndConditions": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- user_settings_page -->' in html
        assert '<a class="nav-link" href="/user/logout">' in html
        users['test_user'] = User.find(username=os.environ['TEST_USERNAME'])
        assert users['test_user'] != None
        assert users['test_user'].validatedEmail == False
        # site.newuser_uploadsdefault has been set to True
        users['test_user'].uploads_enabled == True
        # enable the user. validate the email to continue tests in this module
        users['test_user'].validatedEmail = True
        users['test_user'].save()

class TestUniqueNewUser():
    def test_new_user_form(self, anon_client):
        """ Tests username and email uniqueness
        """
        url = "/user/new"
        response = anon_client.post(
                        url,
                        data = {
                            "username": os.environ['TEST_USERNAME'],
                            "email": os.environ['TEST_USER_EMAIL'],
                            "password": os.environ['TEST_USER_PASSWORD'],
                            "password2": os.environ['TEST_USER_PASSWORD'],
                            "termsAndConditions": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- new_user_form_page -->' in html
        assert html.count('<span class="formError">') == 2
