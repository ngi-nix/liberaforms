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
from flask import current_app
from liberaforms.models.form import Form
from liberaforms.models.answer import AnswerAttachment
from .utils import login

class TestAnswerAttachment():

    def test_create_form_with_file_field(self, client, users, forms):
        """ Creates a form with valid data.
            Tests Preview page and saves form
            Tests for a new FormLog
        """
        login(client, users['editor'])
        slug = "form-with-file-field"
        response = client.get(
                        "/forms/new",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form id="result" method="POST" action="/forms/edit" >' in html
        with open("./assets/form_structure_with_upload.json", 'r') as structure:
            valid_structure = structure.read()
        response = client.post(
                        "/forms/edit",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": slug,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form action="/forms/save" method="post">' in html
        response = client.post(
                        "/forms/save",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        forms['test_form_2'] = Form.find(slug=slug)
        assert forms['test_form_2'] != None
        html = response.data.decode()
        assert '<!-- inspect_form_page -->' in html
        assert forms['test_form_2'].log.count() == 1

    def test_submit_valid_attachment(self, anon_client, forms):
        forms['test_form_2'].enabled = True
        forms['test_form_2'].save()
        form_url = forms['test_form_2'].url
        name = "Julia"
        valid_attachment_name = "valid_attachment.pdf"
        valid_attachment_path = f"./assets/{valid_attachment_name}"
        mimetype = mimetypes.guess_type(valid_attachment_path)
        with open(valid_attachment_path, 'rb') as f:
            stream = BytesIO(f.read())
        valid_file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=valid_attachment_name,
            content_type=mimetype,
        )
        response = anon_client.post(
                        form_url,
                        data = {
                            "text-1620232883208": name,
                            "file-1622045746136": valid_file,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- thank_you_page -->" in html
        answer = forms['test_form_2'].answers[-1]
        assert vars(answer)['data']['text-1620232883208'] == name
        attachment = AnswerAttachment.find(form_id=forms['test_form_2'].id,
                                           answer_id=vars(answer)['id'])
        assert attachment != None
        assert attachment.does_attachment_exist() == True
        assert attachment.file_name == valid_attachment_name

    def test_delete_answer_with_attachment(self, client, forms):
        initial_log_count = forms['test_form_2'].log.count()
        initial_answers_count = forms['test_form_2'].answers.count()
        answer = forms['test_form_2'].answers[-1]
        attachment = AnswerAttachment.find(form_id=forms['test_form_2'].id,
                                           answer_id=vars(answer)['id'])
        response = client.post(
                        f"/forms/delete-answer/{forms['test_form_2'].id}",
                        json = {
                            "id": vars(answer)['id']
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['deleted'] == True
        assert forms['test_form_2'].answers.count() == initial_answers_count - 1
        assert forms['test_form_2'].log.count() == initial_log_count + 1
        assert attachment.does_attachment_exist() == False

    def test_delete_all_answers(self, anon_client, client, forms):
        form_url = forms['test_form_2'].url
        name = "Julia"
        valid_attachment_name = "valid_attachment.pdf"
        valid_attachment_path = f"./assets/{valid_attachment_name}"
        mimetype = mimetypes.guess_type(valid_attachment_path)
        with open(valid_attachment_path, 'rb') as f:
            stream = BytesIO(f.read())
        valid_file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=valid_attachment_name,
            content_type=mimetype,
        )
        response = anon_client.post(
                        form_url,
                        data = {
                            "text-1620232883208": name,
                            "file-1622045746136": valid_file,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- thank_you_page -->" in html
        initial_answers_count = forms['test_form_2'].answers.count()
        initial_log_count = forms['test_form_2'].log.count()
        response = client.get(
                        f"/forms/delete-all-answers/{forms['test_form_2'].id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert f'<div class="title_3">{initial_answers_count}</div>' in html
        response = client.post(
                        f"/forms/delete-all-answers/{forms['test_form_2'].id}",
                        data = {
                            "totalAnswers": initial_answers_count,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
        assert '<!-- list_answers_page -->' in html
        assert forms['test_form_2'].answers.count() == 0
        assert forms['test_form_2'].log.count() == initial_log_count + 1
        assert os.path.isdir(os.path.join(current_app.config['UPLOADS_DIR'],
                                          current_app.config['ATTACHMENT_DIR'],
                                          str(forms['test_form_2'].id))) == False

    @pytest.mark.skip(reason="Unsure")
    def test_submit_invalid_attachment(self, anon_client, forms):
        forms['test_form_2'].enabled = True
        forms['test_form_2'].save()
        form_url = forms['test_form_2'].url
        name = "Stella"
        invalid_attachment_name = "invalid_attachment.ods"
        invalid_attachment_path = f"./assets/{invalid_attachment_name}"
        mimetype = mimetypes.guess_type(invalid_attachment_path)
        with open(invalid_attachment_path, 'rb') as f:
            stream = BytesIO(f.read())
        file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=invalid_attachment_name,
            content_type=mimetype,
        )
        response = anon_client.post(
                        form_url,
                        data = {
                            "text-1620232883208": name,
                            "file-1622045746136": file,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- thank_you_page -->" in html
        answer = forms['test_form_2'].answers[-1]
        assert vars(answer)['data']['text-1620232883208'] == name
        attachment = AnswerAttachment.find(form_id=forms['test_form_2'].id,
                                           answer_id=vars(answer)['id'])
        assert attachment == None
