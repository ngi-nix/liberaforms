"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import pytest
from liberaforms.models.user import User

@pytest.fixture(scope='module')
def new_user():
    user = User(**{
        'username': "dave",
        'email': "dave@example.com",
        'password_hash': "hashed",
        'preferences': {},
        'admin': {},
        'validatedEmail': True,
    })
    return user
