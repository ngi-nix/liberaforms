"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import json
from liberaforms.models.form import Form

class TestNewForm():
    def test_login(self, client, users):
        response = client.post(
                        "/user/login",
                        data = {
                            "username": users['test_user'].username,
                            "password": os.environ['TEST_USER_PASSWORD'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_create_preview_save_form(self, client, forms):
        """ Creates a form with valid data.
            Tests Preview page and saves form
            Tests for a new FormLog
        """
        response = client.get(
                        "/forms/new",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form id="result" method="POST" action="/forms/edit" >' in html
        slug = "a-valid-slug"
        response = client.post(
                        "/forms/edit",
                        data = {
                            "structure": json.dumps({}),
                            "introductionTextMD": "hello",
                            "slug": slug,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form action="/forms/save" method="post">' in html
        response = client.post(
                        "/forms/save",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- inspect_form_page -->' in html
        forms['test_form'] = Form.find(slug=slug)
        assert forms['test_form'].log.count() == 1

    @pytest.mark.skip(reason="TODO")
    def test_valid_slug(self, client):
        initial_slug = forms['test_form'].slug

    def test_toggle_public(self, client, forms):
        """ Tests Form.enabled bool and tests for a new FormLog
        """
        initial_enabled = forms['test_form'].enabled
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/form/toggle-enabled/{forms['test_form'].id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].enabled != initial_enabled
        assert response.json['enabled'] == forms['test_form'].enabled
        assert forms['test_form'].log.count() != initial_log_count
