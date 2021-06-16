"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import werkzeug
from flask import current_app
from liberaforms.models.site import Site
from liberaforms.commands.cryptokey import create as create_cryptokey
from liberaforms.commands.storage import create as create_storage


class TestCommandLine():

    def test_create_cryptokey(self, app):
        """ Tests fernet key generation
        """
        runner = app.test_cli_runner()
        with app.app_context():
            result = runner.invoke(create_cryptokey)
        assert len(result.output) == 49 # len(key)==44. 44 + \n\n = 49


    def test_create_storage(self, app):
        """ Tests local storage directory creation
            Tests remote minio bucket creation if enabled
        """
        assert Site.query.first() != None
        runner = app.test_cli_runner()
        if current_app.config['ENABLE_REMOTE_STORAGE'] == True:
            with app.app_context():
                result = runner.invoke(create_storage, ['--remote-buckets'])
            assert 'for:' in result.output
        else:
            with app.app_context():
                result = runner.invoke(create_storage)
        assert 'Local directories in place' in result.output
        assert os.path.isdir(os.path.join(current_app.config['UPLOADS_DIR'],
                                          current_app.config['MEDIA_DIR'])) == True
        assert os.path.isdir(os.path.join(current_app.config['UPLOADS_DIR'],
                                          current_app.config['BRAND_DIR'])) == True
        assert os.path.isdir(os.path.join(current_app.config['UPLOADS_DIR'],
                                          current_app.config['ATTACHMENT_DIR'])) == True
        if 'FQDN' in os.environ:
            assert os.environ['FQDN'] in current_app.config['MEDIA_DIR']
            assert os.environ['FQDN'] in current_app.config['BRAND_DIR']
            assert os.environ['FQDN'] in current_app.config['ATTACHMENT_DIR']
