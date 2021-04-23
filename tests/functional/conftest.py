"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.site import Site
from tests.unit.conftest import dummy_user as _dummy_user


@pytest.fixture(scope="class")
def site(db):
    return Site.find()
