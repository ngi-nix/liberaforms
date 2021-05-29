"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, logging, datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
#from sqlalchemy import event
from liberaforms import db
from liberaforms.utils.storage.storage import Storage
from liberaforms.utils.database import CRUD
from liberaforms.utils import utils

from pprint import pprint as pp


class Media(db.Model, CRUD, Storage):
    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alt_text = db.Column(db.String, nullable=True)
    file_name = db.Column(db.String, nullable=False)
    storage_name = db.Column(db.String, nullable=False)
    local_filesystem = db.Column(db.Boolean, default=True) #Remote storage = False
    user = db.relationship("User", viewonly=True)

    def __init__(self):
        Storage.__init__(self, public=True)
        self.created = datetime.datetime.now().isoformat()

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    def save_media(self, user, file, alt_text):
        self.user_id = user.id
        self.alt_text = alt_text
        self.file_name = file.filename
        self.storage_name = utils.gen_random_string()
        saved = super().save_file(file, self.storage_name)
        if saved:
            self.save()
        return saved

    def delete_media(self):
        return super().delete_file(self.storage_name)

    def get_url(self):
        host_url = self.user.site.host_url
        return f"{host_url}media/{self.storage_name}"

    def get_media(self):
        bytes = super().get_file(self.storage_name)
        return bytes, self.file_name


#@event.listens_for(AnswerAttachment, "after_delete")
#def delete_answer_attachment(mapper, connection, target):
#    deleted = target.delete_attachment()
