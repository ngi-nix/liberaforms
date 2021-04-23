"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest

from tests.unit.conftest import dummy_user as _dummy_user


@pytest.fixture(scope="class")
def dummy_user(db, _dummy_user):
    _dummy_user.save()
    return _dummy_user



@pytest.fixture(scope='class')
def root_user(db):
    """Returns a root user as defined in ./tests/test.env"""
    email = os.environ['ROOT_USERS'][0]
    username = email.split('@')[0]
    password = "root password"
    admin = User(
        username = username,
        email = email,
        password = password,
        preferences = User.dummy_user_preferences(),
        admin = User.default_admin_settings(),
        validatedEmail = True,
    )
    return admin
