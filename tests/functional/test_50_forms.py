"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import json
from liberaforms.models.form import Form

class TestForm():
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
        with open("./assets/valid_form_structure.json", 'r') as structure:
            valid_structure = structure.read()
        print(valid_structure)
        response = client.post(
                        "/forms/edit",
                        data = {
                            "structure": valid_structure,
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

    @pytest.mark.skip(reason="TODO") # unit test
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
        assert forms['test_form'].log.count() == initial_log_count + 1

    def test_add_editor(self, client, users, forms):
        form_id=forms['test_form'].id
        response = client.get(
                        f"/forms/share/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert f'"/forms/add-editor/{form_id}" method="POST"' in html
        assert '<div id="enabled_links" style="display:None">' in html
        initial_log_count = forms['test_form'].log.count()
        nonexistent_user_email = "nonexistent@example.com"
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
        # use the test admin user as a new editor
        existent_user_email = users['admin'].email
        response = client.post(
                        f"/forms/add-editor/{form_id}",
                        data = {
                            "email": existent_user_email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert f'"/forms/add-editor/{form_id}" method="POST"' in html
        assert existent_user_email in html
        assert forms['test_form'].log.count() == initial_log_count + 1

    def test_toggle_shared_answers(self, client, users, forms):
        form_id=forms['test_form'].id
        initial_enabled = forms['test_form'].sharedEntries['enabled']
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/form/toggle-shared-entries/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].sharedEntries['enabled'] != initial_enabled
        assert response.json['enabled'] == forms['test_form'].sharedEntries['enabled']
        assert forms['test_form'].log.count() == initial_log_count + 1

    def test_toggle_restricted_form_access(self, client, forms):
        form_id=forms['test_form'].id
        initial_restriced_access = forms['test_form'].restrictedAccess
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/form/toggle-restricted-access/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['restricted'] == True
        assert forms['test_form'].restrictedAccess == True
        assert forms['test_form'].log.count() == initial_log_count + 1

    def test_toggle_expiration_notification(self, client, users, forms):
        form_id=forms['test_form'].id
        response = client.get(
                        f"/forms/expiration/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- form_expiration_page -->" in html
        initial_preference = forms['test_form'] \
                             .editors[str(users['test_user'].id)] \
                             ['notification']['expiredForm']
        response = client.post(
                        f"/form/toggle-expiration-notification/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['notification'] != initial_preference
        assert initial_preference != forms['test_form'] \
                                    .editors[str(users['test_user'].id)] \
                                    ['notification']['expiredForm']

    def test_set_expiration_date(self, client, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        invalid_date="2021-00-00"
        response = client.post(
                        f"/forms/set-expiration-date/{form_id}",
                        data = {
                            "date": invalid_date,
                            "time": "00:00"
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['expired'] == False
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == False
        assert forms['test_form'].log.count() == initial_log_count
        valid_past_date="2021-01-01"
        response = client.post(
                        f"/forms/set-expiration-date/{form_id}",
                        data = {
                            "date": valid_past_date,
                            "time": "00:00"
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['expired'] == True
        assert forms['test_form'].has_expired() == True
        assert forms['test_form'].can_expire() == True
        assert forms['test_form'].log.count() != initial_log_count
        initial_log_count = forms['test_form'].log.count()
        valid_future_date="2121-05-05"
        response = client.post(
                        f"/forms/set-expiration-date/{form_id}",
                        data = {
                            "date": valid_future_date,
                            "time": "00:00"
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['expired'] == False
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == True
        assert forms['test_form'].log.count() != initial_log_count
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/forms/set-expiration-date/{form_id}",
                        data = {
                            "date": "",
                            "time": ""
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['expired'] == False
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == False
        assert forms['test_form'].log.count() != initial_log_count

    def test_set_max_answers_expiration(self, client, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        invalid_max_answers = "a"
        response = client.post(
                        f"/forms/set-expiry-total-entries/{form_id}",
                        data = {
                            "total_entries": invalid_max_answers,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == False
        assert forms['test_form'].log.count() == initial_log_count
        valid_max_answers = 3
        response = client.post(
                        f"/forms/set-expiry-total-entries/{form_id}",
                        data = {
                            "total_entries": valid_max_answers,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == True
        assert forms['test_form'].log.count() != initial_log_count
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/forms/set-expiry-total-entries/{form_id}",
                        data = {
                            "total_entries": 0,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == False
        assert forms['test_form'].log.count() != initial_log_count


    def test_save_expired_text(self, client, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
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

    def test_save_after_submit_text(self, client, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
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

    def test_toggle_GDPR_consent(self, client, forms):
        form_id=forms['test_form'].id
        initial_GDPR_state = forms['test_form'].data_consent['enabled']
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/form/toggle-data-consent/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].data_consent['enabled'] == response.json['enabled']
        assert forms['test_form'].data_consent['enabled'] != initial_GDPR_state
        assert forms['test_form'].log.count() != initial_log_count

    def test_recover_GDPR_default_text(self, client, forms):
        form_id=forms['test_form'].id
        text_id=forms['test_form'].data_consent['id']
        initial_log_count = forms['test_form'].log.count()
        response = client.get(
                        f"/forms/default-consent/{form_id}/{text_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert "<h6>" in response.json['html']

    def test_save_GDPR_text(self, client, forms):
        form_id=forms['test_form'].id
        text_id=forms['test_form'].data_consent['id']
        initial_log_count = forms['test_form'].log.count()
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

    def test_view_log(self, client, forms):
        form_id=forms['test_form'].id
        response = client.get(
                        f"/forms/log/list/{form_id}",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- log_list_page -->" in html

    def test_duplicate_form(self, client, forms):
        form_id=forms['test_form'].id
        response = client.get(
                        f"/forms/duplicate/{form_id}",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="info flash_message">' in html
        assert forms['test_form'].introductionText['markdown'] in html
        assert '<input  id="slug" value=""' in html

    def test_toggle_new_answer_notification(self, client, users, forms):
        form_id=forms['test_form'].id
        initial_preference = forms['test_form'] \
                             .editors[str(users['test_user'].id)] \
                             ['notification']['newEntry']
        response = client.post(
                        f"/form/toggle-notification/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert initial_preference != response.json['notification']
        assert initial_preference != forms['test_form'] \
                                     .editors[str(users['test_user'].id)] \
                                     ['notification']['newEntry']
