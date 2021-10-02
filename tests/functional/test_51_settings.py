"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import json
from flask import g
from liberaforms.models.formuser import FormUser
from liberaforms.utils import validators
from .utils import login

class TestFormSettings():
    """ Test the settings an editor can make on a form
    """
    def test_toggle_public(self, client, users, forms):
        """ Tests Form.enabled bool
            Tests for a new FormLog entry
        """
        login(client, users['editor'])
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
        assert forms['test_form'].log.count() == initial_log_count + 1

    def test_save_expired_text(self, users, client, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        login(client, users['editor'])
        response = client.post(
                        f"/forms/save-expired-text/{form_id}",
                        data = {
                            "markdown": "# Hello",
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['html'] == "<h1>Hello</h1>"
        assert forms['test_form'].expired_text_html == response.json['html']
        assert forms['test_form'].log.count() != initial_log_count

    def test_save_after_submit_text(self, users, client, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        login(client, users['editor'])
        response = client.post(
                        f"/forms/save-after-submit-text/{form_id}",
                        data = {
                            "markdown": "# Hello",
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['html'] == "<h1>Hello</h1>"
        assert forms['test_form'].after_submit_text_html == response.json['html']
        assert forms['test_form'].log.count() != initial_log_count

    def test_toggle_GDPR_consent(self, users, client, forms):
        form_id=forms['test_form'].id
        initial_GDPR_state = forms['test_form'].data_consent['enabled']
        initial_log_count = forms['test_form'].log.count()
        login(client, users['editor'])
        response = client.post(
                        f"/form/toggle-data-consent/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].data_consent['enabled'] == response.json['enabled']
        assert forms['test_form'].data_consent['enabled'] != initial_GDPR_state
        assert type(forms['test_form'].data_consent['enabled']) == type(bool())
        assert forms['test_form'].log.count() != initial_log_count

    def test_recover_GDPR_default_text(self, users, client, forms):
        form_id=forms['test_form'].id
        text_id=forms['test_form'].data_consent['id']
        initial_log_count = forms['test_form'].log.count()
        login(client, users['editor'])
        response = client.get(
                        f"/forms/default-consent/{form_id}/{text_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert "<h6>" in response.json['html']

    def test_save_GDPR_text(self, users, client, forms):
        form_id=forms['test_form'].id
        text_id=forms['test_form'].data_consent['id']
        initial_log_count = forms['test_form'].log.count()
        login(client, users['editor'])
        response = client.post(
                        f"/forms/save-consent/{form_id}/{text_id}",
                        data = {
                            "markdown": "# Hello!",
                            "label": "",
                            "required": True
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['html'] == "<h1>Hello!</h1>"
        assert forms['test_form'].data_consent['html'] == response.json['html']
        assert forms['test_form'].log.count() != initial_log_count
        # Test empty markdown input
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/forms/save-consent/{form_id}/{text_id}",
                        data = {
                            "markdown": "",
                            "label": "",
                            "required": True
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert "<h6>" in response.json['html']
        assert forms['test_form'].data_consent['html'] == ""
        assert forms['test_form'].log.count() != initial_log_count

    def test_view_log(self, users, client, forms):
        form_id=forms['test_form'].id
        login(client, users['editor'])
        response = client.get(
                        f"/forms/log/list/{form_id}",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- log_list_page -->" in html

    def test_duplicate_form(self, users, client, forms):
        form_id=forms['test_form'].id
        login(client, users['editor'])
        response = client.get(
                        f"/forms/duplicate/{form_id}",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="info flash_message">' in html
        assert forms['test_form'].introductionText['markdown'] in html
        assert '<input id="slug" value=""' in html

    def test_toggle_new_answer_notification(self, users, client, forms):
        form_id=forms['test_form'].id
        form_user=FormUser.find(form_id=form_id,
                                user_id=g.current_user.id)
        initial_preference = form_user.notifications['newAnswer']
        login(client, users['editor'])
        response = client.post(
                        f"/form/toggle-notification/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert initial_preference != response.json['notification']
        saved_preference = form_user.notifications['newAnswer']
        assert saved_preference != initial_preference
        assert type(saved_preference) == type(bool())

    def test_embed_form_html_code(self, users, client, anon_client, forms):
        form_id = forms['test_form'].id
        login(client, users['editor'])
        response = client.get(
                        f"/forms/view/{form_id}",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert forms['test_form'].embed_url in html
