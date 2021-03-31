"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from .create_admin import create_admin


def register_commands(app):
    app.cli.add_command(create_admin)
