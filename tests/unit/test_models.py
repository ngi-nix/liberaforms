"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os


def test_new_site(new_site):
    """
    GIVEN a Site model
    WHEN a new Site is created
    THEN check the smtpConfig, blurb fields
    """
    assert new_site.smtpConfig['host'] == "smtp.example.com"
    assert "<h1>LiberaForms</h1>" in new_site.blurb['html']

def test_new_user(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, password_hash, and admin fields
    """
    assert new_user.email == os.environ['TEST_USER_EMAIL']
    assert new_user.password_hash[:14] == "$pbkdf2-sha256"
    assert new_user.preferences['language'] == os.environ['DEFAULT_LANGUAGE']
    assert new_user.admin['isAdmin'] == False
