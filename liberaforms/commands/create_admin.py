"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import click
from flask.cli import with_appcontext
from liberaforms import db
from liberaforms.models.user import User
from liberaforms.utils import validators

@click.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.argument("password")
@with_appcontext
def create_admin(username, email, password):
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
    adminSettings["isAdmin"] = True
    admin = User(username = username,
                 email = email,
                 password_hash = validators.hash_password(password),
                 preferences = User.default_user_preferences(),
                 admin = adminSettings,
                 validatedEmail = True,
                 )
    db.session.add(admin)
    db.session.commit()
    print('Admin created: ', admin.id)
