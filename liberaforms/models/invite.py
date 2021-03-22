"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import datetime
from flask_babel import gettext
from sqlalchemy.dialects.postgresql import JSONB
from liberaforms.utils.database import CRUD
from liberaforms import db
from liberaforms.models.site import Site
from liberaforms.utils import utils

class Invite(db.Model, CRUD):
    __tablename__ = "invites"
    id = db.Column(db.Integer, primary_key=True, index=True)
    hostname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=True)
    token = db.Column(JSONB, nullable=False)
    admin = db.Column(db.Boolean)

    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)

    @classmethod
    def create(cls, hostname, email, message, admin=False):
        data={
            "hostname": hostname,
            "email": email,
            "message": message,
            "token": utils.create_token(Invite),
            "admin": admin
        }
        newInvite=Invite(**data)
        newInvite.save()
        return newInvite

    @classmethod
    def find(cls, **kwargs):
        if 'token' in kwargs:
            kwargs={"token__token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    def get_link(self):
        site = Site.find(hostname=self.hostname)
        return "{}user/new/{}".format(site.host_url, self.token['token'])

    def get_message(self):
        return "{}\n\n{}".format(self.message, self.get_link())

    def set_token(self, **kwargs):
        self.invite['token']=utils.create_token(Invite, **kwargs)
        self.save()

    @staticmethod
    def default_message():
        return gettext("Hello,\n\nYou have been invited to LiberaForms.\n\nRegards.")
