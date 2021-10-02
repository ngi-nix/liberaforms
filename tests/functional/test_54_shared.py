"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask import g
from liberaforms.models.user import User
from liberaforms.models.formuser import FormUser
from .utils import login

class TestSharedForm():
    def test_access_shared_forms(self, client, anon_client, users, forms):
        form_id=forms['test_form'].id
        url = f"/forms/share/{form_id}"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['editor'])
        response = client.get(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- share_form_page -->' in html
        assert f'"/forms/add-editor/{form_id}" method="POST"' in html
        assert f'"/forms/add-reader/{form_id}" method="POST"' in html

    def test_add_editor(self, client, users, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        nonexistent_user_email = "nonexistent@example.com"
        login(client, users['editor'])
        response = client.post(
                        f"/forms/add-editor/{form_id}",
                        data = {
                            "email": nonexistent_user_email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert f'"/forms/add-editor/{form_id}" method="POST"' in html
        assert forms['test_form'].log.count() == initial_log_count
        # dummy_1 is already an editor
        dummy_1 = User.find(username=users['dummy_1']['username'])
        assert FormUser.find(form_id=forms['test_form'].id, user_id=dummy_1.id) != None
        existent_user_email = dummy_1.email
        response = client.post(
                        f"/forms/add-editor/{form_id}",
                        data = {
                            "email": existent_user_email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- share_form_page -->' in html
        assert existent_user_email in html
        assert forms['test_form'].log.count() == initial_log_count
        dummy_2 = User.find(username=users['dummy_2']['username'])
        assert dummy_2 != None
        assert FormUser.find(form_id=forms['test_form'].id, user_id=dummy_2.id) == None
        existent_user_email = dummy_2.email
        response = client.post(
                        f"/forms/add-editor/{form_id}",
                        data = {
                            "email": existent_user_email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- share_form_page -->' in html
        assert existent_user_email in html
        assert FormUser.find(form_id=forms['test_form'].id,
                             user_id=dummy_2.id, is_editor=True) != None
        assert forms['test_form'].log.count() == initial_log_count +1

    def test_add_reader(self, client, users, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        nonexistent_user_email = "nonexistent@example.com"
        login(client, users['editor'])
        response = client.post(
                        f"/forms/add-reader/{form_id}",
                        data = {
                            "email": nonexistent_user_email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert f'"/forms/add-reader/{form_id}" method="POST"' in html
        assert forms['test_form'].log.count() == initial_log_count
        # dummy_1 is already a form_user is_editor=True
        dummy_1 = User.find(username=users['dummy_1']['username'])
        assert FormUser.find(form_id=forms['test_form'].id, user_id=dummy_1.id) != None
        existent_user_email = dummy_1.email
        response = client.post(
                        f"/forms/add-reader/{form_id}",
                        data = {
                            "email": existent_user_email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- share_form_page -->' in html
        assert existent_user_email in html
        assert forms['test_form'].log.count() == initial_log_count
        # we delete dummy_2 because it is already and editor
        dummy_2 = User.find(username=users['dummy_2']['username'])
        formuser = FormUser.find(form_id=forms['test_form'].id, user_id=dummy_2.id)
        formuser.delete()
        assert FormUser.find(form_id=forms['test_form'].id, user_id=dummy_2.id) == None
        new_formuser_email = dummy_2.email
        response = client.post(
                        f"/forms/add-reader/{form_id}",
                        data = {
                            "email": new_formuser_email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- share_form_page -->' in html
        assert existent_user_email in html
        assert FormUser.find(form_id=forms['test_form'].id,
                             user_id=dummy_2.id, is_editor=False) != None
        assert forms['test_form'].log.count() == initial_log_count +1


    def test_toggle_restricted_form_access(self, users, client, forms):
        form_id=forms['test_form'].id
        initial_restriced_access = forms['test_form'].restrictedAccess
        initial_log_count = forms['test_form'].log.count()
        login(client, users['editor'])
        response = client.post(
                        f"/form/toggle-restricted-access/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['restricted'] == True
        assert forms['test_form'].restrictedAccess == True
        assert forms['test_form'].log.count() == initial_log_count + 1
