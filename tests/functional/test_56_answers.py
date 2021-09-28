"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.form import Form
from .utils import login


class TestAnswers():
    def test_show_answers_table(self, client, users, forms):
        login(client, users['editor'])
        response = client.get(
                        f"/forms/answers/{forms['test_form'].id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- list_answers_page -->' in html
        assert '<table  id="answersTable"' in html

    def test_show_answers_stats(self, users, client, forms):
        login(client, users['editor'])
        response = client.get(
                        f"/forms/answers/stats/{forms['test_form'].id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- chart_answers_page -->' in html
        assert '<canvas id="time_chart" height="100"></canvas>' in html

    def test_answers_enable_edition(self, users, client, forms):
        login(client, users['editor'])
        response = client.get(
                        f"/forms/answers/{forms['test_form'].id}?edit_mode=true",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<table  id="answersTable"' in html
        assert '<i class="fa fa-trash delete-row-icon enabled"' in html

    def test_download_csv(self, users, client, forms):
        login(client, users['editor'])
        response = client.get(
                        f"/forms/csv/{forms['test_form'].id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'

    def test_delete_answer(self, users, client, forms):
        initial_log_count = forms['test_form'].log.count()
        initial_answers_count = forms['test_form'].answers.count()
        answer_to_delete = forms['test_form'].answers[-1]
        login(client, users['editor'])
        response = client.post(
                        f"/forms/delete-answer/{forms['test_form'].id}",
                        json = {
                            "id": vars(answer_to_delete)['id']
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['deleted'] == True
        assert forms['test_form'].answers.count() == initial_answers_count - 1
        assert forms['test_form'].log.count() == initial_log_count + 1

    def test_toggle_marked_answer(self, users, client, forms):
        answer = forms['test_form'].answers[-1]
        initial_marked = vars(answer)['marked']
        login(client, users['editor'])
        response = client.post(
                        f"/forms/toggle-marked-answer/{forms['test_form'].id}",
                        json = {
                            "id": vars(answer)['id']
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json['marked'] != initial_marked
        assert vars(answer)['marked'] != initial_marked

    @pytest.mark.skip(reason="No way of currently testing this")
    def test_edit_answer_field(self, client, forms):
        pass

    def test_delete_all_answers(self, users, client, forms):
        initial_answers_count = forms['test_form'].answers.count()
        initial_log_count = forms['test_form'].log.count()
        login(client, users['editor'])
        response = client.get(
                        f"/forms/delete-all-answers/{forms['test_form'].id}",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert f'<div class="title_3">{initial_answers_count}</div>' in html
        response = client.post(
                        f"/forms/delete-all-answers/{forms['test_form'].id}",
                        data = {
                            "totalAnswers": initial_answers_count,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
        assert '<!-- list_answers_page -->' in html
        assert forms['test_form'].answers.count() == 0
        assert forms['test_form'].log.count() == initial_log_count + 1
