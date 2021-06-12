"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import click
from flask.cli import AppGroup
from liberaforms.utils.storage.remote import RemoteStorage


storage_cli = AppGroup('storage')


@storage_cli.command()
@click.option('--remote-buckets',
              'remote',
              is_flag=True,
              help="Create buckets on Minio server")
def create(remote):
    if remote:
        (created, msg) = RemoteStorage().create_buckets()
        click.echo(msg)
