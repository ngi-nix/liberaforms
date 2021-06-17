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
    if container_name:
        remote_option = "--remote-buckets" if remote else ""
        flask_cmd = f"docker exec {container_name} flask storage create {remote_option}".split()
        click.echo(" ".join(flask_cmd))
        run_subprocess(flask_cmd)
    else:
        if 'FQDN' in os.environ:
            brand_dir = os.path.join(current_app.config['UPLOADS_DIR'],
                                     current_app.config['BRAND_DIR'])
            if not os.path.isdir(brand_dir):
                shutil.copytree(os.path.join(current_app.config['UPLOADS_DIR'],
                                            'media',
                                            'brand'),
                                brand_dir)
        attachment_dir = os.path.join(current_app.config['UPLOADS_DIR'],
                                      current_app.config['ATTACHMENT_DIR'])
        if not os.path.isdir(attachment_dir):
            os.makedirs(attachment_dir)
        click.echo("Local directories in place")
        if remote:
            (created, msg) = RemoteStorage().create_buckets()
            click.echo(msg)
