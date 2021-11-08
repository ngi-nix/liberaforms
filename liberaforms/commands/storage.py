"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, shutil
import click
import signal, subprocess
from flask import current_app
from flask.cli import AppGroup
from liberaforms.utils.storage.remote import RemoteStorage
from liberaforms.domain import site as site_domain


storage_cli = AppGroup('storage')

def run_subprocess(cmdline):
    try:
        p = subprocess.Popen(cmdline)
        p.wait()
    except KeyboardInterrupt:
        p.send_signal(signal.SIGINT)
        p.wait()

@storage_cli.command()
@click.option('--remote-buckets',
              'remote',
              is_flag=True,
              help="Create buckets on Minio server")
@click.option('--docker-container', 'container_name',
              help="LiberaForms container name")
def create(remote, container_name):
    if not remote:
        return
    if container_name:
        flask_cmd = f"docker exec {container_name} flask storage create --remote-buckets".split()
        click.echo(" ".join(flask_cmd))
        run_subprocess(flask_cmd)
    else:
        (created, msg) = RemoteStorage().create_buckets()
        click.echo(msg)

@storage_cli.command()
@click.option('--email',
              'email',
              help="Send disk usage to this email address")
@click.option('--alert',
              'limit')
def usage(email=None, limit=None):
    if limit and not email:
        click.echo("Missing --email option")
        return
    msg = site_domain.disk_usage(email, limit)
    click.echo(msg)
