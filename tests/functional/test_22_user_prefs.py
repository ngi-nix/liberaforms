"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.utils import validators


class TestUserPreferences():
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
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- change_language_page -->' in html
        initial_language = users['test_user'].preferences['language']
        unavailable_language = 'af' # Afrikaans
        response = client.post(
                        url,
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert users['test_user'].preferences['language'] == initial_language
        available_language = 'ca'
        response = client.post(
                        url,
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert users['test_user'].preferences['language'] == available_language
        users['test_user'].save()

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
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- reset_password_page -->' in html
        password_hash = users['test_user'].password_hash
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
        assert users['test_user'].password_hash == password_hash
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
        # assert users['test_user'].password_hash == validators.hash_password(valid_password)
        assert users['test_user'].password_hash != password_hash
        # reset the password to the value defined in ./tests/test.env. Required by other tests
        password_hash = validators.hash_password(os.environ['TEST_USER_PASSWORD'])
        users['test_user'].password_hash = password_hash
        users['test_user'].save()

    @pytest.mark.skip(reason="No way of currently testing this")
    def test_change_email(self, client):
        """ Not impletmented """
        pass

    def test_toggle_new_answer_default_notification(self, users, client, anon_client):
        """ Tests permission
            # Tests POST only
            Tests toggle bool
        """
        url = "/user/toggle-new-entry-notification"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        #response = client.get(
        #                url,
        #                follow_redirects=True,
        #            )
        #assert response.status_code == 405
        initial_default = users['test_user'].preferences["newEntryNotification"]
        response = client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert users['test_user'].preferences["newEntryNotification"] != initial_default
        assert type(users['test_user'].preferences["newEntryNotification"]) == type(bool())

class TestUserLogout():
    def test_logout(self, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        assert '<a class="nav-link" href="/user/login">' in html
