"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import click
from cryptography.fernet import Fernet
from flask.cli import AppGroup


cryptokey_cli = AppGroup('cryptokey')


@cryptokey_cli.command()
def create():
    key = Fernet.generate_key()
    click.echo(key)
