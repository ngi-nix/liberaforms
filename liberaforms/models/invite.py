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

from pprint import pprint

class Invite(db.Model, CRUD):
    __tablename__ = "invites"
    id = db.Column(db.Integer, primary_key=True, index=True)
    email = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=True)
    token = db.Column(JSONB, nullable=False)
    admin = db.Column(db.Boolean)

    def __init__(self, **kwargs):
        self.email = kwargs["email"]
        self.message = kwargs["message"]
        self.token = kwargs["token"]
        self.admin = kwargs["admin"]

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        filters = []
        if 'token' in kwargs:
            filters.append(cls.token.contains({'token':kwargs['token']}))
            kwargs.pop('token')
        for key, value in kwargs.items():
            filters.append(getattr(cls, key) == value)
        return cls.query.filter(*filters)

    def get_link(self):
        site = Site.find()
        return f"{site.host_url}user/new/{self.token['token']}"

    def get_message(self):
        return f"{self.message}\n\n{self.get_link()}"

    def set_token(self, **kwargs):
        self.invite['token']=utils.create_token(Invite, **kwargs)
        self.save()

    @staticmethod
    def default_message():
        return gettext("Hello,\n\nYou have been invited to LiberaForms.\n\nRegards.")
