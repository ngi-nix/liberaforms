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
from flask import g, current_app
from liberaforms.models.media import Media
from .utils import login, logout


class TestUserMedia():
    def test_media_page(self, users, client, anon_client):
        """ Tests list media page
            Tests permission
        """
        url = f"/user/{users['editor']['username']}/media"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['editor'])
        response = client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- list_media_page -->' in html

    def test_vaild_media_upload(self, users, client, anon_client):
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
        login(client, users['editor'])
        initial_media_count = g.current_user.media.count()
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
        assert g.current_user.media.count() == initial_media_count + 1
        #assert Media.find_all(user_id=g.current_user.id).count() == initial_media_count + 1
        assert response.json['file_name'] == valid_media_name
        media = Media.find(id=1)
        media_path = os.path.join(current_app.config['MEDIA_DIR'], str(g.current_user.id))
        file_path = os.path.join(media_path, media.storage_name)
        thumbnail_path = os.path.join(media_path, f"tn-{media.storage_name}")
        assert os.path.isfile(file_path) == True
        assert os.path.isfile(thumbnail_path) == True

    def test_invaild_media_upload(self, client):
        url = "/media/save"
        invalid_media_name = "invalid_media.json"
        invalid_media_path = f"./assets/{invalid_media_name}"
        with open(invalid_media_path, 'rb') as f:
            stream = BytesIO(f.read())
        mimetype = mimetypes.guess_type(invalid_media_path)
        file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=invalid_media_name,
            content_type=mimetype,
        )
        initial_media_count = g.current_user.media.count()
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
        assert g.current_user.media.count() == initial_media_count

    def test_delete_media(self, client, anon_client):
        media = Media.find(id=1)
        url = media.get_url()
        print(url)
        response = anon_client.get(
                        url
                    )
        print(response)
