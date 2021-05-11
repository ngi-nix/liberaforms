"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest

class TestFormExpiration():
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
        invalid_max_answers = "invalid_integer"
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

    # ./tests/assets/valid_form_structure.json contains a number field
    # with id number-1620224716308
    def test_set_max_number_field_expiration(self, client, forms, number_field_max):
        """ Tests max number fields exipry condition
        """
        form_id = forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        number_field_id = "number-1620224716308"
        response = client.get(
                        f"/forms/expiration/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<input    id="number-1620224716308" type="number"' in html
        response = client.post(
                        f"/forms/set-expiry-field-condition/{form_id}",
                        data = {
                            "field_name": number_field_id,
                            "condition": number_field_max
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['condition'] == str(number_field_max)
        assert response.json['expired'] == False
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == True
        assert forms['test_form'].log.count() == initial_log_count + 1
