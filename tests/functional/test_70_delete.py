"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.user import User
from liberaforms.models.media import Media
from liberaforms.models.form import Form
from liberaforms.models.formuser import FormUser
from liberaforms.models.answer import Answer, AnswerAttachment
from .utils import login, logout

class TestDeleteUser():
    def test_delete_user(self, users, client, anon_client, forms):
        """ Deletes a user with form, attachments, and media
            Creates answers with attachments
            Tests the deletion of the user, media, form, answers and attachments
        """
        """ Create 5 form answers and attachments
        """
        form = Form.find(slug="form-with-file-field")
        form_id = form.id
        user = form.author  # the user we will delete
        user_id = user.id
        attachment_dir = form.get_attachment_dir()
        valid_attachment_name = "valid_attachment.pdf"
        valid_attachment_path = f"./assets/{valid_attachment_name}"
        answer_cnt = 0
        while answer_cnt < 5:
            answer_cnt = answer_cnt +1
            with open(valid_attachment_path, 'rb') as file:
                response = anon_client.post(
                                form.url,
                                data = {
                                    "text-1620232883208": "Julia",
                                    "file-1622045746136": file,
                                },
                                follow_redirects=True,
                            )
            assert response.status_code == 200
            assert form.answers.count() == answer_cnt
            assert len(os.listdir(attachment_dir)) == answer_cnt

        """ Upload media
        """
        login(client, users['editor'])
        url = "/media/save"
        valid_media_name = "valid_media.png"
        valid_media_path = f"./assets/{valid_media_name}"
        initial_media_file_cnt = len(os.listdir(user.get_media_dir()))
        with open(valid_media_path, 'rb') as file:
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
        # both 1. the media file is uploaded and 2. a thumbnail created
        assert initial_media_file_cnt+2 == len(os.listdir(user.get_media_dir()))

        """ Delete user
        """
        delete_user_url = f"/admin/users/delete/{user_id}"
        logout(client)
        login(client, users['admin'])
        response = client.get(
                        delete_user_url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- delete_user_page -->' in html
        assert f'<td>{answer_cnt}</td>' in html
        response = client.post(
                        delete_user_url,
                        data = {
                            "username": user.username,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert FormUser.find_all(user_id=user_id).count() == 0
        assert Form.find_all(author_id=user_id).count() == 0
        assert Answer.find_all(author_id=user_id).count() == 0
        assert '<!-- list_users_page -->' in html
        assert os.path.isdir(user.get_media_dir()) == False
        assert Media.find(user_id=user_id) == None
        assert len(os.listdir(attachment_dir)) == 0
        assert User.find(id=user_id) == None
