"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import click
from flask.cli import AppGroup
#from pathlib import Path
import signal, subprocess
#from dotenv import load_dotenv

#env_path = Path('../') / '.env'
#load_dotenv(dotenv_path="../.env")

database_cli = AppGroup('database')

def run_subprocess(cmdline):
    try:
        p = subprocess.Popen(cmdline)
        p.wait()
    except KeyboardInterrupt:
        p.send_signal(signal.SIGINT)
        p.wait()

@click.group()
def cli():
    pass

@database_cli.command()
@click.option('--docker-container', 'container_name',
              help="PostgreSQL container name")
def create(container_name=None):
    db_name = os.environ['DB_NAME']
    user = os.environ['DB_USER']
    password = os.environ['DB_PASSWORD']

    if container_name:
        pg_cmd = f"docker exec {container_name} psql -U postgres -c".split()
    else:
        pg_cmd = "psql -U postgres -c ".split()

    sql = f"CREATE USER {user} WITH PASSWORD '{password}';"
    cmdline = pg_cmd + [sql]
    click.echo(" ".join(cmdline))
    run_subprocess(cmdline)

    sql = f"CREATE DATABASE {db_name} ENCODING 'UTF8' TEMPLATE template0;"
    cmdline = pg_cmd + [sql]
    click.echo(" ".join(cmdline))
    run_subprocess(cmdline)

    sql = f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user};"
    cmdline = pg_cmd + [sql]
    click.echo(" ".join(cmdline))
    run_subprocess(cmdline)

@database_cli.command()
@click.option('--docker-container', 'container_name',
              help="LiberaForms container name")
def init(container_name=None):
    if container_name:
        flask_cmd = f"docker exec {container_name} flask db".split()
    else:
        flask_cmd = "flask db".split()
    cmdline = flask_cmd + ['init']
    click.echo(" ".join(cmdline))
    run_subprocess(cmdline)

@database_cli.command()
@click.option('--docker-container', 'container_name',
              help="LiberaForms container name")
def update(container_name=None):
    if container_name:
        flask_cmd = f"docker exec {container_name} flask db".split()
    else:
        flask_cmd = "flask db".split()
    cmdline = flask_cmd + ['upgrade']
    click.echo(" ".join(cmdline))
    run_subprocess(cmdline)

@database_cli.command()
@click.option('--docker-container', 'container_name',
              help="PostgreSQL container name")
def drop(container_name=None):
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']

    if container_name:
        pg_cmd = f"docker exec {container_name} psql -U postgres -c".split()
    else:
        pg_cmd = "psql -U postgres -c".split()

    sql = f"DROP DATABASE {db_name};"
    cmdline = pg_cmd + [sql]
    click.echo(" ".join(cmdline))
    run_subprocess(cmdline)

    sql = f"DROP USER IF EXISTS {db_user}"
    cmdline = pg_cmd + [sql]
    click.echo(" ".join(cmdline))
    run_subprocess(cmdline)
