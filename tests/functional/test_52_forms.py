"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import pytest


class TestPublicForm():
    def test_display_form(self, client, forms):
        # test without client login. aka anonymous user
        forms['test_form'].restrictedAccess = False
        forms['test_form'].enabled = False
        forms['test_form'].save()
        form_url = forms['test_form'].url
        print(form_url)
        # test disabled form
        response = client.get(
                        form_url,
                        follow_redirects=True,
                    )
        assert response.status_code == 404
        forms['test_form'].enabled = True
        forms['test_form'].save()
        # test enabled form
        response = client.get(
                        form_url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<meta name="robots" content="noindex">' in html
        assert '"label": "Name", "name": "text-1620232883208"' in html

    def test_submit_form(self, client, forms):
        form_url = forms['test_form'].url
        # submit 4 answers
        names = ["Julia", "Stella", "Jackie", "Vicky"]
        for name in names:
            response = client.post(
                            form_url,
                            data = {
                                "text-1620232883208": name,
                            },
                            follow_redirects=True,
                        )
            assert response.status_code == 200
            html = response.data.decode()
            assert "<!-- thank_you_page -->" in html
            answer = forms['test_form'].answers[-1]
            assert vars(answer)['data']['text-1620232883208'] == name
        assert vars(answer)['marked'] == False
