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
from .utils import login, logout

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
                            "introductionTextMD": "# hello",
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
        assert '<h1>hello</h1>' in forms['test_form'].introductionText['html']
        assert '# hello' in forms['test_form'].introductionText['markdown']
        assert forms['test_form'].introductionText['short_text'] == 'hello'
        html = response.data.decode()
        assert '<!-- inspect_form_page -->' in html
        assert forms['test_form'].log.count() == 1

    def test_initial_values(self, forms):
        assert forms['test_form'].enabled == False
        assert forms['test_form'].users.count() == 1



class TestSlugAvailability():
    def test_slug_availability(self, users, client, forms):
        reserved_slug = current_app.config['RESERVED_SLUGS'][0]
        login(client, users['editor'])
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

    def test_preview_save_form_with_unavailable_slug(self, users, client, forms):
        unavailable_slug = forms['test_form'].slug
        with open("./assets/valid_form_structure.json", 'r') as structure:
            valid_structure = structure.read()
        login(client, users['editor'])
        response = client.post(
                        "/forms/edit",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": unavailable_slug,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 302
        html = response.data.decode()
        assert '/forms/edit</a>' in html
        response = client.post(
                        "/forms/save",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": unavailable_slug,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 302
        html = response.data.decode()
        assert '/forms/edit</a>' in html

    def test_preview_save_form_with_reserved_slug(self, users, client):
        reserved_slug = current_app.config['RESERVED_SLUGS'][0]
        with open("./assets/valid_form_structure.json", 'r') as structure:
            valid_structure = structure.read()
        login(client, users['editor'])
        response = client.post(
                        "/forms/edit",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": reserved_slug,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 302
        html = response.data.decode()
        assert '/forms/edit</a>' in html
        #assert '<form action="/forms/save" method="post">' in html
        response = client.post(
                        "/forms/save",
                        data = {
                            "structure": valid_structure,
                            "introductionTextMD": "hello",
                            "slug": reserved_slug,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 302
        html = response.data.decode()
        assert '/forms/edit</a>' in html
