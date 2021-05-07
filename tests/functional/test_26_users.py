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
from liberaforms.models.invite import Invite
from liberaforms.utils import validators

class TestInvites():
    def test_create_invite(self, admin_client, users, invite):
        """ Test token creation for non admin user
        """
        url = "/admin/invites/new"
        # we create the test_user again, but this time with an invite token
        users['test_user'].delete()
        response = admin_client.post(
                        url,
                        data = {
                            "message": "Hello",
                            "email": os.environ['TEST_USER_EMAIL'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
        assert '<!-- list_invites_page -->' in html
        new_invite = Invite.find(email=os.environ['TEST_USER_EMAIL'])
        assert new_invite != None
        invite['token'] = new_invite.token['token']

    def test_new_user_form_with_invitation(self, client, users, invite):
        token = invite['token']
        url = f"/user/new/{token}"
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
        assert Invite.find_all().count() == 0
        users['test_user'] = User.find(username=os.environ['TEST_USERNAME'])
        assert users['test_user'] != None
        assert users['test_user'].validatedEmail == True
        assert users['test_user'].admin['isAdmin'] == False
        html = response.data.decode()
        assert '<!-- my_forms_page -->' in html
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_create_invite_new_admin(self, anon_client, client,
                                     admin_client, users, invite):
        """ Test token creation for new admin user
            Test permissions
        """
        url = "/admin/invites/new"
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
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- new_invite_page -->' in html
        # we create the test_user again, but this time with an invite admin token
        users['test_user'].delete()
        response = admin_client.post(
                        url,
                        data = {
                            "message": "Hello",
                            "email": os.environ['TEST_USER_EMAIL'],
                            "admin": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
        assert '<!-- list_invites_page -->' in html
        new_invite = Invite.find(email=os.environ['TEST_USER_EMAIL'])
        assert new_invite != None
        invite['token'] = new_invite.token['token']

    def test_new_user_form_with_admin_invitation(self, client, users, invite):
        token = invite['token']
        url = f"/user/new/{token}"
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
        assert Invite.find_all().count() == 0
        users['test_user'] = User.find(username=os.environ['TEST_USERNAME'])
        assert users['test_user'] != None
        assert users['test_user'].validatedEmail == True
        assert users['test_user'].admin['isAdmin'] == True
        html = response.data.decode()
        assert '<!-- my_forms_page -->' in html
        assert '<a class="nav-link" href="/user/logout">' in html
        # remove admin permission from test user to continue testing
        users['test_user'].admin['isAdmin'] = False
        users['test_user'].save()
