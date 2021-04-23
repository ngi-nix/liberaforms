"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os


def test_landing(db, client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode()
    assert '<div id="blurb" class="marked-up">' in html
