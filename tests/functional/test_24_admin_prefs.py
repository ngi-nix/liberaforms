"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import ast
import pytest
from flask import g
from liberaforms.utils import utils
from .utils import login, logout


class TestAdmin():
    """ Tests admin's admin preferences
    """
    def test_toggle_new_user_notification(self, users, client, anon_client):
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
        login(client, users['admin'])
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 405
        notification = g.current_user.admin["notifyNewUser"]
        response = client.post(url)
        assert response.status_code == 200
        assert g.current_user.admin["notifyNewUser"] != notification
        assert type(g.current_user.admin["notifyNewUser"]) == type(bool())

    def test_toggle_new_form_notification(self, users, client, anon_client):
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
        login(client, users['admin'])
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        #print(utils.print_obj_values(g.current_user))
        #assert g.current_user.username == users['admin']['username']
        assert response.status_code == 405
        notification = g.current_user.admin["notifyNewForm"]
        response = client.post(url)
        assert response.status_code == 200
        assert g.current_user.admin["notifyNewForm"] != notification
        assert type(g.current_user.admin["notifyNewForm"]) == type(bool())

    def test_toggle_newuser_uploadsenabled(self, users, client, anon_client):
        pass
