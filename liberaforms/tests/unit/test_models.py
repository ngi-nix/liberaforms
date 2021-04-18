"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
from liberaforms.tests.unit import new_user


def test_new_user(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, password_hash, and admin fields
    """
    assert new_user.email == 'dave@example.com'
    assert new_user.password_hash != 'super_secret'
    assert new_user.preferences['language'] == os.environ['DEFAULT_LANGUAGE']
    assert new_user.admin['isAdmin'] == False
