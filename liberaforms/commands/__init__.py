"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from .site import site_cli
from .smtp import smtp_cli
from .user import user_cli
from .database import database_cli
from .config import config_cli
from .cryptokey import cryptokey_cli
from .storage import storage_cli


def register_commands(app):
    app.cli.add_command(site_cli)
    app.cli.add_command(smtp_cli)
    app.cli.add_command(user_cli)
    app.cli.add_command(database_cli)
    app.cli.add_command(config_cli)
    app.cli.add_command(cryptokey_cli)
    app.cli.add_command(storage_cli)
