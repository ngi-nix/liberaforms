"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask import g
from liberaforms.models.user import User
from liberaforms.utils import validators
from .utils import login, logout


class TestUserPreferences():
    def test_cli_user_create(self, app, users, client):
        """ Login the created user dummy_1
            Tests user preferences
            Logout dummy_1
        """

        response = login(client, users['dummy_1'])
        assert "<!-- list_templates_page -->" in response.data.decode()

    def test_change_language(self, users, client, anon_client):
        """ Tests unavailable language and available language
            as defined in ./liberaforms/config.py
            Tests permission
        """
        url = "/user/change-language"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['dummy_1'])
        dummy_1 = User.find(username=users['dummy_1']['username'])
        response = client.get(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- change_language_page -->' in html
        initial_language = dummy_1.preferences['language']
        unavailable_language = 'af' # Afrikaans
        response = client.post(
                        url,
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert dummy_1.preferences['language'] == initial_language
        available_language = 'ca'
        response = client.post(
                        url,
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert dummy_1.preferences['language'] == available_language
        dummy_1.save()

    def test_change_password(self, users, client, anon_client):
        """ Tests invalid and valid password
            as defined in ./liberaforms/utils/validators.py
            Tests permission
        """
        url = "/user/reset-password"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['dummy_1'])
        dummy_1 = User.find(username=users['dummy_1']['username'])
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- reset_password_page -->' in html
        initial_password_hash = dummy_1.password_hash
        invalid_password="1234"
        response = client.post(
                        url,
                        data = {
                            "password": invalid_password,
                            "password2": invalid_password
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert dummy_1.password_hash == initial_password_hash
        valid_password="this is another valid password"
        response = client.post(
                        url,
                        data = {
                            "password": valid_password,
                            "password2": valid_password
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert dummy_1.password_hash != initial_password_hash
        # reset the password to the value defined in ./tests/test.env. Required by other tests
        #password_hash = validators.hash_password(users['editor']['password'])
        dummy_1.password_hash = initial_password_hash
        dummy_1.save()


    @pytest.mark.skip(reason="No way of currently testing this")
    def test_change_email(self, client):
        """ Not impletmented """
        pass

    def test_toggle_new_answer_default_notification(self, users, client, anon_client):
        """ Tests permission
            # Tests POST only
            Tests toggle bool
        """
        url = "/user/toggle-new-answer-notification"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html

        login(client, users['dummy_1'])
        dummy_1 = User.find(username=users['dummy_1']['username'])
        initial_default = dummy_1.preferences["newAnswerNotification"]
        response = client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert dummy_1.preferences["newAnswerNotification"] != initial_default
        assert type(dummy_1.preferences["newAnswerNotification"]) == type(bool())

        #logout(client)
        #user=User.find(username=users['dummy_1']['username'])
        #user.delete()
