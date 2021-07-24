"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.user import User
from liberaforms.models.form import Form
from liberaforms.models.answer import Answer, AnswerAttachment
from liberaforms.models.log import FormLog

class TestDeleteUser():
    def test_delete_user(self, client, anon_client, admin_client, forms):
        """ Uses form with slug: form-with-file-field
            Creates answers with attachments
            Deletes the user
            Tests the deletion of the user, form, answers and attachments
        """
        form = Form.find(slug="form-with-file-field")
        attachment_dir = form.get_attachment_dir()
        valid_attachment_name = "valid_attachment.pdf"
        valid_attachment_path = f"./assets/{valid_attachment_name}"
        """ Create 5 answers
        """
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

        """ Delete user
        """
        user = form.author
        user_id = user.id
        delete_user_url = f"/admin/users/delete/{user_id}"
        response = admin_client.get(
                        delete_user_url,
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- delete_user_page -->' in html
        assert f'<td>{answer_cnt}</td>' in html
        form_id = form.id
        response = admin_client.post(
                        delete_user_url,
                        data = {
                            "username": user.username,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- list_users_page -->' in html
        assert Form.find(id=form_id) == None
        assert Answer.find(form_id=form_id) == None
        assert AnswerAttachment.find(form_id=form_id) == None
        assert len(os.listdir(attachment_dir)) == 0
        assert User.find(id=user_id) == None
