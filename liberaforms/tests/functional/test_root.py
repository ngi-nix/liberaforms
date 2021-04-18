"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms.tests.functional import client

def test_landing(client):
    landing = client.get("/")
    assert landing.status_code == 200
    html = landing.data.decode()
    assert '<a class="navbar-brand" href="/"><img src="/favicon.png" /></a>' in html
