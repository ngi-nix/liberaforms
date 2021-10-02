"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import click
from pprint import pprint
from flask import current_app
from flask.cli import with_appcontext
from flask.cli import AppGroup
from liberaforms.models.site import Site
from liberaforms.utils.dispatcher.dispatcher import Dispatcher

smtp_cli = AppGroup('smtp')


@smtp_cli.command()
@with_appcontext
def get():
    site = Site.find()
    if not site:
        click.echo("Site not found")
        return
    pprint(site.smtpConfig)

@smtp_cli.command()
@click.option('-recipient', 'recipient', help="Recipient email address")
@with_appcontext
def test(recipient):
    site = Site.find()
    if not site:
        click.echo("Site not found")
        return
    with current_app.test_request_context():
        status = Dispatcher().send_test_email(recipient)
        pprint(status)

@smtp_cli.command()
@click.option('-host', 'host', help="SMTP provider FQDN")
@click.option('-port', 'port', help="SMTP port number")
@click.option('-user', 'user', help="SMTP username")
@click.option('-password', 'password', help="SMTP password")
@click.option('-encryption', 'encryption', help="SMTP encryption [ SSL | STARTTLS | ]")
@click.option('-noreply', 'noreply', help="Emails are sent from this address")
@with_appcontext
def set(host, port, user, password, noreply, encryption=None):
    try:
        port = int(port) if port else None
    except:
        click.echo("Port must be a number")
        return
    site = Site.find()
    if not site:
        click.echo("Site not found")
        return
    smtp_config = {
        "host": host,
        "port": port,
        "user": user if user else "",
        "password": password if password else "",
        "encryption": encryption if encryption else "",
        "noreplyAddress": noreply
    }
    site.smtpConfig = smtp_config
    site.save()
    pprint(site.smtpConfig)
    click.echo("SMTP set ok")
