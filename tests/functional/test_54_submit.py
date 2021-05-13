"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest

class TestPublicForm():
    def test_display_form(self, anon_client, forms):
        # test without client login. aka anonymous user
        forms['test_form'].restrictedAccess = False
        forms['test_form'].enabled = False
        forms['test_form'].save()
        form_url = forms['test_form'].url
        print(form_url)
        # test disabled form
        response = anon_client.get(
                        form_url,
                        follow_redirects=True,
                    )
        assert response.status_code == 404
        forms['test_form'].enabled = True
        forms['test_form'].save()
        # test enabled form
        response = anon_client.get(
                        form_url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<meta name="robots" content="noindex">' in html
        assert '"label": "Name", "name": "text-1620232883208"' in html

    def test_submit_form(self, anon_client, forms):
        form_url = forms['test_form'].url
        name = "Julia"
        response = anon_client.post(
                        form_url,
                        data = {
                            "text-1620232883208": name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- thank_you_page -->" in html
        assert forms['test_form'].after_submit_text_html in html
        answer = forms['test_form'].answers[-1]
        assert vars(answer)['data']['text-1620232883208'] == name
        assert vars(answer)['marked'] == False

    def test_sumbit_embedded_form(self, anon_client, forms):
        original_skip_emails = os.environ['SKIP_EMAILS']
        os.environ['SKIP_EMAILS'] = 'True'
        embedded_form_url = forms['test_form'].embed_url
        response = anon_client.get(embedded_form_url)
        assert response.status_code == 200
        html = response.data.decode()

        assert '"label": "Name", "name": "text-1620232883208"' in html
        name = "Felicitat"
        response = anon_client.post(
                        embedded_form_url,
                        data = {
                            "text-1620232883208": name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- thank_you_page -->" in html
        assert forms['test_form'].after_submit_text_html in html
        answer = forms['test_form'].answers[-1]
        assert vars(answer)['data']['text-1620232883208'] == name
        os.environ['SKIP_EMAILS'] = original_skip_emails

    def test_max_number_field_expiration(self, anon_client, forms, number_field_max):
        original_skip_emails = os.environ['SKIP_EMAILS']
        os.environ['SKIP_EMAILS'] = 'True'
        form_url = forms['test_form'].url
        number_field_id = "number-1620224716308"
        number_to_submit = 2
        names = ["Stella", "Debbie", "Jackie"]
        # the form should not exipire after three submits because:
        # len(names) * number_to_submit < number_field_max
        for name in names:
            response = anon_client.post(
                            form_url,
                            data = {
                                "text-1620232883208": name,
                                number_field_id: number_to_submit
                            },
                            follow_redirects=True,
                        )
            assert response.status_code == 200
            html = response.data.decode()
            assert "<!-- thank_you_page -->" in html
            answer = forms['test_form'].answers[-1]
            assert vars(answer)['data']['text-1620232883208'] == name
        assert vars(answer)['marked'] == False
        assert forms['test_form'].has_expired() == False
        name = "Vicky"
        # the form should exipire
        response = anon_client.post(
                        form_url,
                        data = {
                            "text-1620232883208": name,
                            number_field_id: number_to_submit
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- thank_you_page -->" in html
        assert forms['test_form'].has_expired() == True
        os.environ['SKIP_EMAILS'] = original_skip_emails

    def test_number_field(self, client, users, anon_client, forms):
        assert forms['test_form'].expired == True
        form_url = forms['test_form'].url
        name = "Rita"
        response = anon_client.post(
                        form_url,
                        data = {
                            "text-1620232883208": name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- form_has_expired_page -->" in html
        assert forms['test_form'].expired_text_html in html
        # Remove the max number_field expiry condition for the next test
        client.post(
            "/user/login",
            data = {
                "username": users['test_user'].username,
                "password": os.environ['TEST_USER_PASSWORD'],
            },
        )
        form_id = forms['test_form'].id
        number_field_id = "number-1620224716308"
        response = client.post(
                        f"/forms/set-expiry-field-condition/{form_id}",
                        data = {
                            "field_name": number_field_id,
                            "condition": ""
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert forms['test_form'].has_expired() == False

    def test_max_answers(self, anon_client, forms, max_answers):
        original_skip_emails = os.environ['SKIP_EMAILS']
        os.environ['SKIP_EMAILS'] = 'True'
        form_url = forms['test_form'].url
        assert forms['test_form'].answers.count() < max_answers
        name = "Julia"
        while forms['test_form'].answers.count() < max_answers:
            assert forms['test_form'].has_expired() == False
            response = anon_client.post(
                            form_url,
                            data = {
                                "text-1620232883208": name,
                            },
                            follow_redirects=True,
                        )
            assert response.status_code == 200
            html = response.data.decode()
            assert "<!-- thank_you_page -->" in html
        assert forms['test_form'].answers.count() == max_answers
        assert forms['test_form'].has_expired() == True
        response = anon_client.post(
                        form_url,
                        data = {
                            "text-1620232883208": name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- form_has_expired_page -->" in html
        os.environ['SKIP_EMAILS'] = original_skip_emails
