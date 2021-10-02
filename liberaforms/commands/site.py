"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import click
from flask.cli import with_appcontext
from flask.cli import AppGroup
from liberaforms.models.site import Site

site_cli = AppGroup('site')


@site_cli.command()
@click.option('-hostname', 'hostname', help="FQDN")
@click.option('-scheme', 'scheme', help="[ http | https ]")
@click.option('-port', 'port', help="port number")
@with_appcontext
def set(hostname=None, scheme=None, port=None):
    if not (scheme and (scheme == 'http' or scheme == 'https')):
        click.echo("Scheme required. http or https")
        return
    try:
        port = int(port) if port else None
    except:
        click.echo("Port must be a number")
        return
    site = Site.find()
    if not site:
        if not hostname:
            click.echo("FQDN hostname required")
            return
        site = Site(hostname, scheme, port)
    else:
        site.port = port
        site.scheme = scheme
        site.hostname = hostname if hostname else site.hostname
    site.save()
    site_url = f"{site.scheme}://{site.hostname}"
    if site.port:
        site_url = f"{site_url}:{site.port}"
    click.echo(site_url)
    click.echo("Site set ok")
