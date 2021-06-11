"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from .user import user_cli
from .database import database_cli
from .config import config_hint_cli
from .cryptokey import cryptokey_cli


def register_commands(app):
    app.cli.add_command(user_cli)
    app.cli.add_command(database_cli)
    app.cli.add_command(config_hint_cli)
    app.cli.add_command(cryptokey_cli)
