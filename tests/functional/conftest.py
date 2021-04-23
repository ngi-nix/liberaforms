"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest

from tests.unit.conftest import default_user


@pytest.fixture(scope="class")
def saved_user(db, default_user):
    default_user.save()
    return default_user
