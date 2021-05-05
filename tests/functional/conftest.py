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
    }
