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
        assert len(result.output) == 45

    @pytest.mark.skipif(os.environ['ENABLE_REMOTE_STORAGE'] != 'True',
                        reason="ENABLE_REMOTE_STORAGE=False in test.ini")

    def test_create_remote_storage(self, app):
        """ Tests local storage directory creation
            Tests remote minio bucket creation if enabled
        """
        assert Site.query.first() != None
        runner = app.test_cli_runner()
        with app.app_context():
            result = runner.invoke(create_storage, ['--remote-buckets'])
        assert 'for:' in result.output
