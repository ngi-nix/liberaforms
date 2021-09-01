"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask import g
from liberaforms.models.user import User
from .utils import login, logout


class TestAdminUsers():
    """ The admin can set some users' properties. Test those.
    """
    def test_toggle_admin(self, users, client, anon_client):
        """ Test permissions
            Test toggle admin
        """
        #login(client, users['admin'])

        users['tested_user'] = User.find(username=users['editor']['username'])
        url = f"/admin/users/toggle-admin/{users['tested_user'].id}"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['editor'])
        response = client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        initial_is_admin = users['tested_user'].admin['isAdmin']
        logout(client)
        login(client, users['admin'])
        response = client.post(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json == {"admin": users['tested_user'].admin['isAdmin']}
        assert initial_is_admin != users['tested_user'].admin['isAdmin']
        # reset user.admin['isAdmin'] to continue testing
        users['tested_user'].admin['isAdmin'] = False
        users['tested_user'].save()

    def test_toggle_uploads(self, users, client, anon_client):
        """ Test permissions
            Test toggle
        """
        url = f"/admin/users/toggle-uploads-enabled/{users['tested_user'].id}"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['editor'])
        response = client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        initial_uploads_enabled = users['tested_user'].uploads_enabled
        logout(client)
        login(client, users['admin'])
        response = client.post(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json == {"uploads_enabled": users['tested_user'].uploads_enabled}
        assert initial_uploads_enabled != users['tested_user'].uploads_enabled
        # set user.uploads_enabled to False to continue testing
        users['tested_user'].uploads_enabled = False
        users['tested_user'].save()
