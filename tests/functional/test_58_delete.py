"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.form import Form
from liberaforms.models.answer import Answer
from liberaforms.models.log import FormLog

class TestDeleteForm():
    def test_login(self, client, users):
        #pytest.exit("stopped before deleting forms")
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

    def test_delete_form(self, client, forms):
        form_id = forms['test_form'].id
        initial_answers_count = forms['test_form'].answers.count()
        response = client.get(
                        f"/forms/delete/{form_id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- delete_form_page -->' in html
        assert f'<span class="highlightedText">{initial_answers_count}' in html
        # test incorrect slug
        response = client.post(
                        f"/forms/delete/{forms['test_form'].id}",
                        data = {
                            "slug": f"{forms['test_form'].slug}-wrong"
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- delete_form_page -->' in html
        # test correct slug
        response = client.post(
                        f"/forms/delete/{forms['test_form'].id}",
                        data = {
                            "slug": forms['test_form'].slug
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- my_forms_page -->' in html
        assert Form.find(id=form_id) == None
        assert Answer.find(form_id=form_id) == None
        assert FormLog.find(form_id=form_id) == None
