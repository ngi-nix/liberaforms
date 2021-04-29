"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, sys
import click
from pathlib import Path
from flask import current_app
from flask.cli import AppGroup
from jinja2 import Environment, FileSystemLoader

config_hint_cli = AppGroup('config')

@config_hint_cli.command()
@click.argument("configuration")
def hint(configuration):
    installation_path = os.path.join(current_app.root_path, '../')
    installation_path = os.path.abspath(installation_path)
    gunicorn_py = os.path.join(installation_path, 'gunicorn.py')
    template_dir = os.path.dirname(os.path.realpath(__file__))
    template_dir = os.path.join(template_dir, 'templates')
    j2_env = Environment(loader = FileSystemLoader(template_dir))
    python_bin_dir = Path(sys.executable).parent

    if configuration == "gunicorn":
        template = j2_env.get_template('gunicorn.j2')
        config = template.render({
                    'pythonpath': installation_path,
                    'gunicorn_bin': f"{python_bin_dir}/gunicorn",
                    'username': os.environ.get('USER')
                })
        click.echo(f"Suggested config for {gunicorn_py}\n")
        click.echo(f"{config}{os.linesep}")
        click.echo(f"Test with: gunicorn -c {gunicorn_py} 'wsgi:create_app()'")

    if configuration == "supervisor":
        template = j2_env.get_template('supervisor.j2')
        supervisor_config = template.render({
                    'installation_path': installation_path,
                    'gunicorn_bin': f"{python_bin_dir}/gunicorn",
                    'gunicorn_py': gunicorn_py,
                    'username': os.environ.get('USER')
                })
        click.echo("Suggested config for /etc/supervisor/conf.d/liberaforms.conf\n")
        click.echo(f"{supervisor_config}{os.linesep}")
