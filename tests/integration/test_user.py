"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from tests.unit.conftest import new_user


def test_save_user(new_user):
    new_user.save()
    assert new_user.id != None
