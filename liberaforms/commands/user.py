"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import click
from flask.cli import AppGroup
from flask.cli import with_appcontext
from liberaforms import db
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
    if not validators.is_valid_email(email):
        print("Not a valid email")
        return
    if User.find(username=username):
        print("User already exists")
        return
    if User.find(email=email):
        print("User with email already exists")
        return
    adminSettings = User.default_admin_settings()
    adminSettings["isAdmin"] = is_admin
    user = User(username = username,
                email = email,
                password_hash = validators.hash_password(password),
                preferences = User.default_user_preferences(),
                admin = adminSettings,
                validatedEmail = True,
                )
    db.session.add(user)
    db.session.commit()
    if is_admin:
        print('Admin created: ', user.id)
    else:
        print('User created: ', user.id)

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
