"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest

class TestFormAdminSettings():
    def test_disable_form(self, client, admin_client, anon_client, forms):
        """ Tests disable form
            Test permissions
        """
        form_id = forms['test_form'].id
        url = f"/admin/forms/toggle-public/{form_id}"
        response = anon_client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- inspect_form_page -->' in html
        assert forms['test_form'].adminPreferences['public'] == False
        assert forms['test_form'].is_public() == False
        response = anon_client.get(
                            f"/{forms['test_form'].slug}",
                            follow_redirects=True
                        )
        assert response.status_code == 404
        html = response.data.decode()
        assert '<!-- page_not_found_404 -->' in html
        forms['test_form'].adminPreferences['public'] = True
        forms['test_form'].save()

    def test_change_author(self, client, admin_client, anon_client, forms, users):
        """ Tests nonexistent username and valid username
            Test permission
        """
        form_id = forms['test_form'].id
        url = f"/admin/forms/change-author/{form_id}"
        response = anon_client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        assert '<!-- site_index_page -->' in response.data.decode()
        response = client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        assert '<!-- site_index_page -->' in response.data.decode()
        response = admin_client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        assert '<!-- change_author_page -->' in response.data.decode()
        initial_author = forms['test_form'].author
        assert str(initial_author.id) in forms['test_form'].editors.keys()
        nonexistent_username = "nonexistent"
        response = admin_client.post(
                            url,
                            data = {
                                "old_author_username": initial_author.username,
                                "new_author_username": nonexistent_username,
                            },
                            follow_redirects=False
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- change_author_page -->' in html
        assert '<div class="warning flash_message">' in html
        # we use the admin user to be the new author
        assert users['admin'].username != initial_author.username
        response = admin_client.post(
                            url,
                            data = {
                                "old_author_username": initial_author.username,
                                "new_author_username": users['admin'].username,
                            },
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
        assert '<!-- inspect_form_page -->' in html
        assert forms['test_form'].author.id == users['admin'].id
        assert str(initial_author.id) not in forms['test_form'].editors.keys()
        assert str(users['admin'].id) in forms['test_form'].editors.keys()
        # reset author to initial value to continue testing
        response = admin_client.post(
                            url,
                            data = {
                                "old_author_username": users['admin'].username,
                                "new_author_username": initial_author.username,
                            },
                            follow_redirects=True
                        )
