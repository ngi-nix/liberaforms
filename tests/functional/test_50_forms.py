"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import json
from flask import g, current_app
from liberaforms.models.form import Form
from liberaforms.utils import validators
from .utils import login

class TestForm():
    def test_create_preview_save_form_1(self, client, users, forms):
        """ Creates a form with valid data.
            Tests Preview page and saves form
            Tests for a new FormLog
        """
        login(client, users['editor'])
        response = client.get(
                        "/forms/new",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form id="result" method="POST" action="/forms/edit" >' in html
        slug = "a-valid-slug"
        with open("./assets/valid_form_structure.json", 'r') as structure:
            valid_structure = structure.read()
        #print(valid_structure)
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
        forms['test_form'] = Form.find(slug=slug)
        assert forms['test_form'] != None
        html = response.data.decode()
        assert '<!-- inspect_form_page -->' in html
        assert forms['test_form'].log.count() == 1

    def test_initial_values(self, forms):
        assert forms['test_form'].enabled == False
        assert forms['test_form'].sharedAnswers['enabled'] == False
        assert validators.is_valid_UUID(forms['test_form'].sharedAnswers['key']) == True
        assert forms['test_form'].shared_notifications == []

    def test_create_preview_save_form_2(self, client, forms):
        """ Creates a form with valid data.
            Tests Preview page and saves form
            Tests for a new FormLog
        """
        slug = "another-valid-slug"
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




class TestSlugAvailability():
    def test_slug_availability(self, client, forms):
        reserved_slug = current_app.config['RESERVED_SLUGS'][0]
        response = client.post(
                        "/forms/check-slug-availability",
                        data = {
                            "slug": reserved_slug,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['available'] == False
        unavailable_slug = forms['test_form'].slug
        response = client.post(
                        "/forms/check-slug-availability",
                        data = {
                            "slug": unavailable_slug,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['available'] == False

    def test_preview_save_form_with_reserved_slug(self, client):
        reserved_slug = current_app.config['RESERVED_SLUGS'][0]
        with open("./assets/valid_form_structure.json", 'r') as structure:
            valid_structure = structure.read()
        response = client.post(
                        "/forms/edit",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": reserved_slug,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        #print(html)
        assert '<!-- edit_form_page -->' in html
        #assert '<form action="/forms/save" method="post">' in html
        response = client.post(
                        "/forms/save",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": reserved_slug,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="error flash_message">' in html
        assert '<!-- edit_form_page -->' in html

    def test_preview_save_form_with_unavailable_slug(self, client, forms):
        unavailable_slug = forms['test_form'].slug
        with open("./assets/valid_form_structure.json", 'r') as structure:
            valid_structure = structure.read()
        response = client.post(
                        "/forms/edit",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": unavailable_slug,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        #assert '<form action="/forms/save" method="post">' in html
        assert '<!-- edit_form_page -->' in html
        response = client.post(
                        "/forms/save",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": unavailable_slug,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        #assert '<div class="error flash_message">' in html
        assert '<!-- edit_form_page -->' in html
