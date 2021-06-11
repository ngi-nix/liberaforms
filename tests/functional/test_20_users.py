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
    """ Creates the 'editor' user
    """
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
        """ Creates the first non-admin user
            Saves to database
        """
        url = "/user/new"
        response = client.post(
                        url,
                        data = {
                            "username": users['editor']['username'],
                            "email": users['editor']['email'],
                            "password": users['editor']['password'],
                            "password2": users['editor']['password'],
                            "termsAndConditions": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- user_settings_page -->' in html
        assert '<a class="nav-link" href="/user/logout">' in html
        user = User.find(username=users['editor']['username'])
        assert user != None
        assert user.validatedEmail == False
        # site.newuser_enableuploads has been set to True
        user.uploads_enabled == True
        # enable the user. validate the email to continue tests in this module
        user.validatedEmail = True
        user.save()


class TestUniqueNewUser():
    def test_new_user_form(self, anon_client):
        """ Tests username and email uniqueness
        """
        url = "/user/new"
        response = anon_client.post(
                        url,
                        data = {
                            "username": os.environ['USER1_USERNAME'],
                            "email": os.environ['USER1_EMAIL'],
                            "password": os.environ['USER1_PASSWORD'],
                            "password2": os.environ['USER1_PASSWORD'],
                            "termsAndConditions": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- new_user_form_page -->' in html
        assert html.count('<span class="formError">') == 2
