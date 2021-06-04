"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.site import Site


@pytest.fixture(scope="class")
def site(db):
    return Site.find()

@pytest.fixture(scope="session")
def forms():
    return {
        'test_form': None,
        'test_form_2': None,
    }

@pytest.fixture(scope='module')
def client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="module")
def invite():
    return {
        'id': None,
        'token': None,
    }

# value used to test number field expiration
@pytest.fixture(scope="module")
def number_field_max():
    return 7

@pytest.fixture(scope="module")
def max_answers():
    return 10
