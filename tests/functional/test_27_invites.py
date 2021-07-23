"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.user import User
from liberaforms.models.invite import Invite


class TestInvites():
    def test_create_invite_1(self, client, anon_client,
                             admin_client, users, invite):
        """ Test invite new non admin user
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

        # TODO: test invitation to existing email

        response = admin_client.post(
                        url,
                        data = {
                            "message": "Hello",
                            "email": users['dummy_1']['email'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        if not os.environ['SKIP_EMAILS']:
            assert 'Recipient address rejected' in html
        else:
            assert '<div class="success flash_message">' in html
        assert '<!-- list_invites_page -->' in html
        new_invite = Invite.find(email=users['dummy_1']['email'])
        assert new_invite != None
        invite['id'] = new_invite.id
        invite['token'] = new_invite.token['token']

    def test_delete_invite_1(self, admin_client, invite):
        url = f"/admin/invites/delete/{invite['id']}"
        response = admin_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
        assert '<!-- list_invites_page -->' in html
        assert Invite.find_all().count() == 0

    def test_create_invite_2(self, admin_client, users, invite):
        url = "/admin/invites/new"
        response = admin_client.post(
                        url,
                        data = {
                            "message": "Hello",
                            "email": users['dummy_1']['email'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        new_invite = Invite.find(email=users['dummy_1']['email'])
        assert new_invite != None
        invite['id'] = new_invite.id
        invite['token'] = new_invite.token['token']

    def test_new_user_form_with_invitation(self, client, users, invite):
        token = invite['token']
        url = f"/user/new/{token}"
        response = client.post(
                        url,
                        data = {
                            "username": users['dummy_1']['username'],
                            "email": users['dummy_1']['email'],
                            "password": users['dummy_1']['password'],
                            "password2": users['dummy_1']['password'],
                            "termsAndConditions": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert Invite.find(id=invite['id']) == None
        user = User.find(username=users['dummy_1']['username'])
        assert user != None
        assert user.validatedEmail == True
        assert user.admin['isAdmin'] == False
        html = response.data.decode()
        assert '<!-- user_settings_page -->' in html
        assert '<a class="nav-link" href="/user/logout">' in html
        # delete test_user to continue testing
        user.delete()
        assert User.find(id=user.id) == None

    def test_create_invite_new_admin(self, anon_client, client,
                                     admin_client, users, invite):
        """ Test token creation for new admin user
        """
        url = "/admin/invites/new"
        response = admin_client.post(
                        url,
                        data = {
                            "message": "Hello",
                            "email": users['dummy_1']['email'],
                            "admin": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        if not os.environ['SKIP_EMAILS']:
            assert 'Recipient address rejected' in html
        else:
            assert '<div class="success flash_message">' in html
        assert '<!-- list_invites_page -->' in html
        new_invite = Invite.find(email=users['dummy_1']['email'])
        assert new_invite != None
        invite['token'] = new_invite.token['token']

    def test_new_user_form_with_admin_invitation(self, client, users, invite):
        token = invite['token']
        url = f"/user/new/{token}"
        response = client.post(
                        url,
                        data = {
                            "username": users['dummy_1']['username'],
                            "email": users['dummy_1']['email'],
                            "password": users['dummy_1']['password'],
                            "password2": users['dummy_1']['password'],
                            "termsAndConditions": True,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert Invite.find_all().count() == 0
        user = User.find(username=users['dummy_1']['username'])
        assert user != None
        assert user.validatedEmail == True
        assert user.admin['isAdmin'] == True
        html = response.data.decode()
        assert '<!-- user_settings_page -->' in html
        assert '<a class="nav-link" href="/user/logout">' in html
        # remove admin permission from test user to continue testing
        user.admin['isAdmin'] = False
        user.save()

        #pytest.exit("invite tests completed")
