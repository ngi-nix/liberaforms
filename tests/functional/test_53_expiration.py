"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask import g
from liberaforms.models.formuser import FormUser
from .utils import login, logout

class TestFormExpiration():
    def test_toggle_expiration_notification(self, client, users, forms):
        form_id=forms['test_form'].id
        login(client, users['editor'])
        response = client.get(
                        f"/forms/expiration/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- form_expiration_page -->" in html
        form_user=FormUser.find(form_id=form_id,
                                user_id=g.current_user.id)
        initial_preference = form_user.notifications['expiredForm']
        response = client.post(
                        f"/form/toggle-expiration-notification/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['notification'] != initial_preference
        assert initial_preference != form_user.notifications['expiredForm']

    def test_set_expiration_date(self, users, client, anon_client, forms):
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        invalid_date="2021-00-00"
        login(client, users['editor'])
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
        assert forms['test_form'].log.count() == initial_log_count +1
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
        assert forms['test_form'].log.count() == initial_log_count +1
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
        assert forms['test_form'].log.count() == initial_log_count +1

    def test_set_max_answers_expiration(self, users, client, forms):
        """ Tests valid max answers exipry condition value
            Tests invalid max answers exipry condition value
        """
        form_id=forms['test_form'].id
        initial_log_count = forms['test_form'].log.count()
        valid_max_answers = 12
        login(client, users['editor'])
        response = client.post(
                        f"/forms/set-expiry-total-answers/{form_id}",
                        data = {
                            "total_answers": valid_max_answers,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['total_answers'] == valid_max_answers
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == True
        assert forms['test_form'].log.count() == initial_log_count +1
        initial_log_count = forms['test_form'].log.count()
        invalid_max_answers = "invalid_integer"
        response = client.post(
                        f"/forms/set-expiry-total-answers/{form_id}",
                        data = {
                            "total_answers": invalid_max_answers,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['total_answers'] == 0
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == False
        assert forms['test_form'].expiryConditions['totalAnswers'] == 0
        assert forms['test_form'].log.count() == initial_log_count +1
        initial_log_count = forms['test_form'].log.count()
        response = client.post(
                        f"/forms/set-expiry-total-answers/{form_id}",
                        data = {
                            "total_answers": invalid_max_answers,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == False
        assert forms['test_form'].log.count() == initial_log_count +1

    # ./tests/assets/valid_form_structure.json contains a number field
    # with id number-1620224716308
    def test_set_max_number_field_expiration(self, users, client, forms):
        """ Tests for max_number_field input in html
            Tests valid max answers exipry condition value
            Tests invalid max answers exipry condition value
        """
        form_id = forms['test_form'].id
        number_field_id = "number-1620224716308"
        login(client, users['editor'])
        response = client.get(
                        f"/forms/expiration/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert f'<input    id="{number_field_id}" type="number"' in html
        url = f"/forms/set-expiry-field-condition/{form_id}"
        initial_log_count = forms['test_form'].log.count()
        valid_max_number = 31
        response = client.post(
                        url,
                        data = {
                            "field_name": number_field_id,
                            "condition": valid_max_number
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['condition'] == str(valid_max_number)
        assert response.json['expired'] == False
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == True
        field_condition = {'type': 'number', 'condition': valid_max_number}
        assert forms['test_form'].expiryConditions['fields'][number_field_id] == field_condition
        assert forms['test_form'].log.count() == initial_log_count + 1
        initial_log_count = forms['test_form'].log.count()
        invalid_max_number = "invalid_integer"
        response = client.post(
                        url,
                        data = {
                            "field_name": number_field_id,
                            "condition": invalid_max_number
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['condition'] == 0
        assert response.json['expired'] == False
        assert forms['test_form'].has_expired() == False
        assert forms['test_form'].can_expire() == False
        assert forms['test_form'].expiryConditions['fields'] == {}
        assert forms['test_form'].log.count() == initial_log_count + 1

    def test_set_expirations(self, users, client, forms, max_answers, number_field_max):
        """ Set up expiration conditions for submit tests to be made later
            No assertions are made in this function. (previously tested)
            This is the last function in this module.
        """
        form_id = forms['test_form'].id
        number_field_id = "number-1620224716308"
        valid_max_answers = max_answers
        login(client, users['editor'])
        response = client.post(
                        f"/forms/set-expiry-total-answers/{form_id}",
                        data = {
                            "total_answers": valid_max_answers,
                        },
                        follow_redirects=False,
                    )
        valid_max_number = number_field_max
        response = client.post(
                        f"/forms/set-expiry-field-condition/{form_id}",
                        data = {
                            "field_name": number_field_id,
                            "condition": valid_max_number
                        },
                        follow_redirects=False,
                    )
