"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.user import User
from liberaforms.models.site import Site


@pytest.fixture(scope='module')
def new_site(app):
    with app.app_context():
        site = Site(
            hostname = "example.com",
            port = 80,
            scheme = "http",
        )
        return site

@pytest.fixture(scope='session')
def test_user():
    """ The default test user as defined in ./tests/test.ini
    """
    user = User(
        username = os.environ['TEST_USERNAME'],
        email = os.environ['TEST_USER_EMAIL'],
        password = os.environ['TEST_USER_PASSWORD'],
        preferences = User.default_user_preferences(),
        admin = User.default_admin_settings(),
        validatedEmail = True,
        uploadsEnabled = False
    )
    return user
