"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import werkzeug
from io import BytesIO
from liberaforms.models.site import Site
from .utils import login, logout


class TestSiteConfig():
    def test_uploads_tree(self, app):
        assert os.path.isdir(os.path.join(app.config['UPLOADS_DIR'],
                                          app.config['MEDIA_DIR'])) == True
        assert os.path.isdir(os.path.join(app.config['UPLOADS_DIR'],
                                          app.config['BRAND_DIR'])) == True
        assert os.path.isdir(os.path.join(app.config['UPLOADS_DIR'],
                                          app.config['ATTACHMENT_DIR'])) == True
        if 'FQDN' in os.environ:
            assert os.environ['FQDN'] in app.config['MEDIA_DIR']
            assert os.environ['FQDN'] in app.config['BRAND_DIR']
            assert os.environ['FQDN'] in app.config['ATTACHMENT_DIR']

    def test_site_default_values(self, app):
        pass

    def test_change_sitename(cls, site, users, admin_client, anon_client):
        login(admin_client, users['admin'])
        url = "/site/change-sitename"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' not in html
        initial_sitename = site.siteName
        new_name = "New name!!"
        response = admin_client.post(
                        "/site/change-sitename",
                        data = {
                            "sitename": new_name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.siteName != initial_sitename

    def test_change_default_language(cls, site, admin_client, anon_client):
        """ Tests unavailable language and available language
            as defined in ./liberaforms/config.py
            Tests admin permission
        """
        url = "/site/change-default-language"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        initial_language = site.defaultLanguage
        response = admin_client.get(
                        url,
                        follow_redirects=False,
                    )
        html = response.data.decode()
        assert '<!-- change_language_page -->' in html
        unavailable_language = 'af' # Afrikaans
        response = admin_client.post(
                        url,
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage == initial_language
        available_language = 'ca'
        response = admin_client.post(
                        url,
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage == available_language

    def test_toggle_invitation_only(cls, site, admin_client, anon_client):
        url = "/site/toggle-invitation-only"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        invitation_only = site.invitationOnly
        response = admin_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.invitationOnly != invitation_only

    @pytest.mark.skip(reason="TODO")
    def test_set_consent_texts(cls, admin_client):
        pass

    def test_change_primary_color(cls, site, admin_client, anon_client):
        """ Tests valid and invalid html hex color
            Tests admin permission
        """
        url = "/site/primary-color"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        url,
                        follow_redirects=False,
                    )
        html = response.data.decode()
        assert '<div class="menu-color-options">' in html
        initial_color = site.primary_color
        bad_color = "green"
        response = admin_client.post(
                        url,
                        data = {
                            "hex_color": bad_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.primary_color == initial_color
        html = response.data.decode()
        assert '<div class="menu-color-options">' in html
        valid_color = "#cccccc"
        response = admin_client.post(
                        url,
                        data = {
                            "hex_color": valid_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.primary_color != initial_color
        html = response.data.decode()
        assert '<div id="site_settings"' in html

    def test_change_logo(self, app, admin_client, anon_client):
        """ Tests valid and invalid image files in ./tests/assets
            Tests jpeg to png logo conversion
            Tests favicon creation
            Tests admin permission
        """
        url = "/site/change-icon"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                    url,
                    follow_redirects=False,
                )
        html = response.data.decode()
        assert '<!-- change_icon_page -->' in html
        brand_dir = os.path.join(app.config['UPLOADS_DIR'],
                                 app.config['BRAND_DIR'])
        logo_path = os.path.join(brand_dir, 'logo.png')
        favicon_path = os.path.join(brand_dir, 'favicon.ico')
        initial_logo_stats = os.stat(logo_path)
        initial_favicon_stats = os.stat(favicon_path)
        invalid_logo = "invalid_logo.jpeg"
        #invalid_favicon = "favicon_invalid.jpeg"
        with open(f'./assets/{invalid_logo}', 'rb') as f:
            stream = BytesIO(f.read())
        invalid_file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=invalid_logo,
            content_type="plain/txt",
        )
        response = admin_client.post(
                    url,
                    data = {
                        'file': invalid_file,
                    },
                    follow_redirects=True,
                    content_type='multipart/form-data',
                )
        assert response.status_code == 200
        assert initial_logo_stats.st_size == os.stat(logo_path).st_size
        assert initial_favicon_stats.st_size == os.stat(favicon_path).st_size
        html = response.data.decode()
        assert '<!-- change_icon_page -->' in html
        valid_logo = "valid_logo.jpeg"
        with open(f'./assets/{valid_logo}', 'rb') as f:
            stream = BytesIO(f.read())
        valid_file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=valid_logo,
            content_type="image/png",
        )
        response = admin_client.post(
                    url,
                    data = {
                        'file': valid_file,
                    },
                    follow_redirects=True,
                    content_type='multipart/form-data',
                )
        assert response.status_code == 200
        assert initial_logo_stats.st_size != os.stat(logo_path).st_size
        assert initial_favicon_stats.st_size != os.stat(favicon_path).st_size
        html = response.data.decode()
        assert '<!-- admin-panel_page -->' in html

    def test_restore_default_logo(self, app, admin_client, anon_client):
        url = "/site/reset-favicon"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        brand_dir = os.path.join(app.config['UPLOADS_DIR'],
                                 app.config['BRAND_DIR'])
        logo_path = os.path.join(brand_dir, 'logo.png')
        default_logo_path = os.path.join(brand_dir, 'logo-default.png')
        favicon_path = os.path.join(brand_dir, 'favicon.ico')
        default_favicon_path = os.path.join(brand_dir, 'favicon-default.ico')
        initial_logo_stats = os.stat(logo_path)
        initial_favicon_stats = os.stat(favicon_path)
        response = admin_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert initial_logo_stats.st_size != os.stat(logo_path).st_size
        assert os.stat(logo_path).st_size == os.stat(default_logo_path).st_size
        assert initial_favicon_stats.st_size != os.stat(favicon_path).st_size
        assert os.stat(favicon_path).st_size == os.stat(default_favicon_path).st_size
        html = response.data.decode()
        assert '<div id="site_settings"' in html

    def test_toggle_newuser_enableuploads(self, site, admin_client, anon_client):
        """ Tests permissions
            Tests toggle
        """
        url = "/site/toggle-newuser-uploads-default"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        initial_newuser_enableuploads = site.newuser_enableuploads
        response = admin_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert response.json == {"uploads": site.newuser_enableuploads}
        assert initial_newuser_enableuploads != site.newuser_enableuploads

    def test_edit_public_link_creation(self, site, admin_client, anon_client):
        """ Tests valid and invalid ports
            Tests admin permission
        """
        response = anon_client.get(
                        "/site/edit-host-url",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        "/site/edit-host-url",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<span id="site_scheme">' in html
        # toggle site_scheme
        initial_scheme = site.scheme
        response = admin_client.post(
                    '/site/toggle-scheme',
                    follow_redirects=True,
                )
        assert response.status_code == 200
        assert site.scheme != initial_scheme
        # change port
        initial_port = site.port
        invalid_port = "i_am_a_string"
        response = admin_client.post(
                    f'/site/change-port/{invalid_port}',
                    follow_redirects=True,
                )
        assert response.status_code == 400
        assert site.port == initial_port
        valid_port = 5555
        response = admin_client.post(
                    f'/site/change-port/{valid_port}',
                    follow_redirects=True,
                )
        assert response.status_code == 200
        assert site.port != initial_port

    def test_edit_blurb(self, site, admin_client, anon_client):
        """ Posts markdown and tests resulting HTML and short_text
            Tests admin permission
        """
        url = "/site/save-blurb"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.post(
                    url,
                    data = {
                        'editor': "# Tested !!\nline1\nline2",
                    },
                    follow_redirects=True,
                )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<h1>Tested !!</h1>' in html
        assert '<p>line1<br />\nline2</p>' in html
        assert '<h1>Tested !!</h1>' in site.blurb['html']
        assert '# Tested !!' in site.blurb['markdown']
        assert 'Tested !!' in site.blurb['short_text']

    def test_save_smtp_config(self, site, admin_client):
        """ Tests invalid and valid smtp configuration
            Tests admin permission
        """
        initial_smtp_config = site.smtpConfig
        response = admin_client.get(
                        "/site/email/config",
                        follow_redirects=False,
                    )
        html = response.data.decode()
        assert '<form method="POST" action="/site/email/config">' in html
        invalid_smtp_conf = {
            'host': 'smtp.example.com',
            'port': "i_am_a_string",
            'encryption': 'SSL',
            'user': 'username',
            'password': 'password',
            'noreplyAddress': 'noreply@example.com'
        }
        response = admin_client.post(
                        "/site/email/config",
                        data = invalid_smtp_conf,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.smtpConfig == initial_smtp_config
        html = response.data.decode()
        assert '<form method="POST" action="/site/email/config">' in html
        valid_smtp_conf = {
            'host': os.environ['TEST_SMTP_HOST'],
            'port': int(os.environ['TEST_SMTP_PORT']),
            'encryption': os.environ['TEST_SMTP_ENCRYPTION'],
            'user': os.environ['TEST_SMTP_USERNAME'],
            'password': os.environ['TEST_SMTP_USER_PASSWORD'],
            'noreplyAddress': os.environ['TEST_SMTP_NO_REPLY']
        }
        response = admin_client.post(
                        "/site/email/config",
                        data = valid_smtp_conf,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.smtpConfig['host'] == os.environ['TEST_SMTP_HOST']
        assert site.smtpConfig['port'] == int(os.environ['TEST_SMTP_PORT'])
        assert site.smtpConfig['encryption'] == os.environ['TEST_SMTP_ENCRYPTION']
        assert site.smtpConfig['user'] == os.environ['TEST_SMTP_USERNAME']
        assert site.smtpConfig['password'] == os.environ['TEST_SMTP_USER_PASSWORD']
        assert site.smtpConfig['noreplyAddress'] == os.environ['TEST_SMTP_NO_REPLY']

    @pytest.mark.skipif(os.environ['SKIP_EMAILS'] == 'True',
                        reason="SKIP_EMAILS=True in test.ini")
    def test_test_smtp_config(self, site, admin_client, users):
        """ Sends a test email to admin user
        """
        response = admin_client.post(
                        "site/email/test-config",
                        data = {
                            'email': users['admin']['email'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
