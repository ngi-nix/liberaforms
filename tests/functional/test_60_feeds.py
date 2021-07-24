"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest

class TestFeeds():
    def test_rss_feed(self, anon_client):
        """ Test the generation of an RSS response
        """
        response = anon_client.get(
                        "/feed/rss",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert response.mimetype == "application/rss+xml"
        data = response.data.decode()
        assert "<?xml version=\'1.0\' encoding=\'UTF-8\'?>" in data

    def test_atom_feed(self, anon_client):
        """ Test the generation of an RSS response
        """
        response = anon_client.get(
                        "/feed/atom",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert response.mimetype == "application/atom+xml"
        data = response.data.decode()
        assert "<?xml version=\'1.0\' encoding=\'UTF-8\'?>" in data
