"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, logging, datetime
import pathlib
from PIL import Image
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
#from sqlalchemy import event
from werkzeug.datastructures import FileStorage
from flask import current_app
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

    def save_media(self, user, file, alt_text, storage_name=None):
        self.user_id = user.id
        self.alt_text = alt_text
        self.file_name = file.filename
        if not storage_name:
            extension = pathlib.Path(self.file_name).suffix
            self.storage_name = f"{utils.gen_random_string()}{extension}"
        else:
            self.storage_name = storage_name
        saved = super().save_file(file, self.storage_name)
        if saved:
            self.save()
            self.save_thumbnail()
        return saved

    def delete_media(self):
        Storage.__init__(self, public=True)
        removed = super().delete_file(self.storage_name)
        if removed:
            self.delete_thumbnail()
            self.delete()
            return True
        return False

    def get_url(self):
        host_url = self.user.site.host_url
        return f"{host_url}file/{self.storage_name}"

    def get_media(self):
        bytes = super().get_file(self.storage_name)
        return bytes, self.file_name

    def save_thumbnail(self):
        try:
            storage_name = f"tn-{self.storage_name}"
            tmp_thumbnail_path = os.path.join(current_app.config['TMP_DIR'],
                                              storage_name)
            (stream, file_name) = self.get_media()
            with open(tmp_thumbnail_path, "wb") as outfile:
                #Copy the BytesIO stream to the output file
                outfile.write(stream.getbuffer())
            image = Image.open(tmp_thumbnail_path)
            image.thumbnail((50,50))
            image.save(tmp_thumbnail_path)
            storage = Storage(public=True)
            storage.save_file(tmp_thumbnail_path, storage_name, sub_dir="")
        except Exception as error:
            logging.warning(f"Could not create thumbnail: {error}")

    def delete_thumbnail(self):
        storage_name = f"tn-{self.storage_name}"
        return super().delete_file(storage_name)

    def get_thumbnail_url(self):
        host_url = self.user.site.host_url
        storage_name = f"tn-{self.storage_name}"
        return f"{host_url}file/{storage_name}"


#@event.listens_for(AnswerAttachment, "after_delete")
#def delete_answer_attachment(mapper, connection, target):
#    deleted = target.delete_attachment()
