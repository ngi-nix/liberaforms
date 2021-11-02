"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import click
from flask.cli import AppGroup
from flask.cli import with_appcontext
from liberaforms.models.site import Site
from liberaforms.models.user import User
from liberaforms.utils import validators

user_cli = AppGroup('user')

@user_cli.command()
@click.option('-admin', 'is_admin', is_flag=True, help="Make this user and admin")
@click.argument("username")
@click.argument("email")
@click.argument("password")
@with_appcontext
def create(username, email, password, is_admin):
    #if not validators.is_valid_email(email):
    #    click.echo("Not a valid email")
    #    return False
    if User.find(username=username):
        click.echo("User already exists")
        return False
    if User.find(email=email):
        click.echo("User with email already exists")
        return False
    adminSettings = User.default_admin_settings()
    adminSettings["isAdmin"] = is_admin
    user = User(username = username,
                email = email,
                password = password,
                preferences = User.default_user_preferences(),
                admin = adminSettings,
                validatedEmail = True,
                uploads_enabled = Site.find().newuser_enableuploads,
                )
    user.save()
    if is_admin:
        print(f'Admin created OK. id: {user.id}')
    else:
        print(f'User created OK. id: {user.id}')
    return True

@user_cli.command()
@click.argument("username")
@with_appcontext
def disable(username):
    user = User.find(username=username)
    if not user:
        click.echo("User not found")
    user.blocked=True
    user.save()
    click.echo(f"{username} disabled")

@user_cli.command()
@click.argument("username")
@with_appcontext
def enable(username):
    user = User.find(username=username)
    if not user:
        click.echo("User not found")
    user.blocked=False
    user.save()
    click.echo(f"{username} enabled")
