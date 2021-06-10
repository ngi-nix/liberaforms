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
from liberaforms.models.user import User
from liberaforms.models.media import Media
from liberaforms.commands.user import create as create_user
from .utils import login, logout


class TestUserMedia():

    @pytest.mark.skipif(os.environ['ENABLE_REMOTE_STORAGE'] != 'True',
                        reason="ENABLE_REMOTE_STORAGE!=True in test.ini")
    def test_ensure_bucket(self):
        from liberaforms.utils.storage.remote import RemoteStorage
        assert RemoteStorage().ensure_buckets_exist() == True

    def test_media_page(self, users, client, anon_client):
        """ Tests list media page
            Tests permission
        """
        login(client, users['editor'])
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
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['editor'])
        file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=valid_media_name,
            content_type=mimetype,
        )
        initial_media_count = g.current_user.media.count()
        response = client.post(
                        url,
                        data = {
                            'media_file': file,
                            'alt_text': "valid alternative text",
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['file_name'] == valid_media_name
        assert g.current_user.media.count() == initial_media_count + 1
        media = Media.find(id=1)
        media_path = os.path.join(current_app.config['MEDIA_DIR'], str(g.current_user.id))
        file_path = os.path.join(media_path, media.storage_name)
        thumbnail_path = os.path.join(media_path, f"tn-{media.storage_name}")
        assert media.does_media_exits() == True
        assert media.does_media_exits(thumbnail=True) == True

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

    @pytest.mark.skip(reason="TODO")
    def test_view_media(self, client, anon_client, users):
        user = User.find(username=users['editor']['username'])
        media = Media.find_all(user_id=user.id).first()
        url = media.get_url()
        response = anon_client.get(
                        url
                    )
        print(response)

    def test_delete_media(self, app, client, anon_client, users):
        """ Tests delete media
            Tests Permissions
        """
        user = User.find(username=users['editor']['username'])
        media = Media.find_all(user_id=user.id).first()
        url = f"media/delete/{media.id}"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        runner = app.test_cli_runner()
        with app.app_context():
            result = runner.invoke(create_user, [users['dummy_1']['username'],
                                                 users['dummy_1']['email'],
                                                 users['dummy_1']['password']
                                                 ])
        logout(client)
        response = login(client, users['dummy_1'])
        assert g.current_user.username == users['dummy_1']['username']
        dummy_1 = User.find(username=users['dummy_1']['username'])
        response = client.post(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json == False
        assert '<!-- site_index_page -->' in html
        dummy_1.delete()
        login(client, users['editor'])
        response = client.post(
                        url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
