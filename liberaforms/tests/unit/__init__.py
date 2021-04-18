"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import pytest
from liberaforms.models.user import User
#from liberaforms.models.site import Site

@pytest.fixture(scope='module')
def new_user():
    user = User(
        username = "dave",
        email = "dave@example.com",
        password = "super_secret",
        preferences = User.default_user_preferences(),
        admin = User.default_admin_settings(),
        validatedEmail = True,
    )
    return user
