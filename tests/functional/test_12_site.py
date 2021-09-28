"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import werkzeug
from io import BytesIO
from .utils import login, logout


class TestSiteStatistics():
    def test_site_stats_graph(cls, users, site, anon_client, client):
        """ Tests site statistics page
            Only tests if the page was generated
            Tests permissions
        """
        url = "/site/stats"
        response = anon_client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html

        #response = client.get(
        #                    url,
        #                    follow_redirects=True
        #                )
        #assert response.status_code == 200
        #html = response.data.decode()
        #assert '<!-- site_index_page -->' in html
        
        login(client, users['admin'])
        response = client.get(
                        url,
                        follow_redirects=True
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_stats_page -->' in html
