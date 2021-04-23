"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest #, logging


#@pytest.mark.usefixtures('saved_user')
class TestUser():

    def test_saved_user(self, saved_user):
        assert saved_user.id != None

    def test_login(self, client, saved_user):
        """ Tests bad credentials and good credentials """
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

    def test_change_language(self, saved_user, client):
        """ Tests unavailable language and available language
            as defined in ./liberaforms/config.py
        """
        #with caplog.at_level(logging.WARNING, logger="app.access"):
        unavailable_language = 'af' # Afrikaans
        response = client.post(
                        "/user/change-language",
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert saved_user.preferences['language'] != unavailable_language

        available_language = 'ca'
        response = client.post(
                        "/user/change-language",
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert saved_user.preferences['language'] == available_language
        saved_user.save()

    def test_change_password(self, saved_user, client):
        """ Tests bad password and good password
            as defined in ./liberaforms/utils/validators.py
        """
        password_hash = saved_user.password_hash
        bad_password="1234"
        response = client.post(
                        "/user/reset-password",
                        data = {
                            "password": bad_password,
                            "password2": bad_password
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert saved_user.password_hash == password_hash
        good_password="this is a good password"
        response = client.post(
                        "/user/reset-password",
                        data = {
                            "password": good_password,
                            "password2": good_password
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert saved_user.password_hash != password_hash

    @pytest.mark.skip(reason="No way of currently testing this")
    def test_change_email(self, client):
        """ Not impletmented """
        pass

    def test_new_answer_default_notification(self, saved_user, client):
        current_default = saved_user.preferences["newEntryNotification"]
        response = client.post(
                        "/user/toggle-new-entry-notification",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert saved_user.preferences["newEntryNotification"] != current_default


    def test_logout(self, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/login">' in html
