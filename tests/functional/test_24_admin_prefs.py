"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import ast
import pytest


class TestAdmin():
    def test_toggle_new_user_notification(self, users, admin_client, anon_client):
        """ Tests admin permission
            Tests POST only
            Tests toggle bool
        """
        url = "/admin/toggle-newuser-notification"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 405
        notification = users['admin'].admin["notifyNewUser"]
        response = admin_client.post(url)
        assert response.status_code == 200
        assert users['admin'].admin["notifyNewUser"] != notification
        assert type(users['admin'].admin["notifyNewUser"]) == type(bool())

    def test_toggle_new_form_notification(self, users, admin_client, anon_client):
        """ Tests admin permission
            Tests POST only
            Tests toggle bool
        """
        url = "/admin/toggle-newform-notification"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 405
        notification = users['admin'].admin["notifyNewForm"]
        response = admin_client.post(url)
        assert response.status_code == 200
        assert users['admin'].admin["notifyNewForm"] != notification
        assert type(users['admin'].admin["notifyNewForm"]) == type(bool())
