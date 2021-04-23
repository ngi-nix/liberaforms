"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest

class TestSiteConfig():

    def test_login_admin(cls, users, client):
        response = client.post(
                        "/user/login",
                        data = {
                            "username": users['admin'].username,
                            "password": users["admin_password"],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- my_forms_page -->" in html
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_change_sitename(cls, site, client):
        sitename = site.siteName
        new_name = "New name!!"
        response = client.post(
                        "/site/change-sitename",
                        data = {
                            "sitename": new_name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.siteName != sitename

    def test_change_default_language(cls, site, client):
        """ Tests unavailable language and available language
            as defined in ./liberaforms/config.py
        """
        language = site.defaultLanguage
        unavailable_language = 'af' # Afrikaans
        response = client.post(
                        "/site/change-default-language",
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage == language
        available_language = 'ca'
        response = client.post(
                        "/site/change-default-language",
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage != language

    def test_toggle_invitation_only(cls, site, client):
        invitation_only = site.invitationOnly
        response = client.post(
                        "/site/toggle-invitation-only",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.invitationOnly != invitation_only

    @pytest.mark.skip(reason="No way of currently testing this")
    def test_set_consent_texts(cls, client):
        pass

    def test_change_menucolor(cls, site, client):
        """ Tests valid and invalid html hex color
        """
        color = site.menuColor
        bad_color = "green"
        response = client.post(
                        "/site/change-menu-color",
                        data = {
                            "hex_color": bad_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.menuColor == color
        good_color = "#cccccc"
        response = client.post(
                        "/site/change-menu-color",
                        data = {
                            "hex_color": good_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.menuColor != color

    def test_logout_admin(cls, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div id="blurb" class="marked-up">' in html
        assert '<a class="nav-link" href="/user/login">' in html
