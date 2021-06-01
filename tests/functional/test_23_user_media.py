"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import werkzeug
from io import BytesIO
import mimetypes
from liberaforms.models.media import Media
#from liberaforms.utils import validators


class TestUserMedia():
    def test_media_page(self, users, client, anon_client):
        """ Tests list media page
            Tests permission
        """
        url = f"/user/{users['test_user'].username}/media"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- list_media_page -->' in html

    def test_media_upload(self, users, client, anon_client):
        """ Tests media upload
            Tests permission
        """
        url = "/media/save"
        valid_media_name = "valid_media.png"
        valid_media_path = f"./assets/{valid_media_name}"
        with open(valid_media_path, 'rb') as f:
            stream = BytesIO(f.read())
        mimetype = mimetypes.guess_type(valid_media_path)
        file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=valid_media_name,
            content_type=mimetype,
        )
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        initial_media_count = users['test_user'].media.count()
        response = client.post(
                        url,
                        data = {
                            'file': file,
                            'alt_text': "valid alternative text",
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert users['test_user'].media.count() == initial_media_count + 1
        #assert Media.find_all(user_id=users['test_user'].id).count() == initial_media_count + 1
        assert response.json['file_name'] == valid_media_name


class TestUserLogout():
    def test_logout(self, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        assert '<a class="nav-link" href="/user/login">' in html
