"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import werkzeug
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

    @pytest.mark.skipif(os.environ['ENABLE_REMOTE_STORAGE'] != 'True',
                        reason="ENABLE_REMOTE_STORAGE!=True in test.ini")
    def test_create_bucket(self, app):
        """ Tests remote minio bucket creation
            Creates the buckets. Buckets are used by other tests
        """
        runner = app.test_cli_runner()
        with app.app_context():
            result = runner.invoke(create_storage, ['--remote-buckets'])
        assert 'Buckets ok.' in result.output
