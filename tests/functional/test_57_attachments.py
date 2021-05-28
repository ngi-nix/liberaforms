"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest


class TestAnswerAttachment():

    def test_login(self, client, users):
        response = client.post(
                        "/user/login",
                        data = {
                            "username": users['test_user'].username,
                            "password": os.environ['TEST_USER_PASSWORD'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/logout">' in html
