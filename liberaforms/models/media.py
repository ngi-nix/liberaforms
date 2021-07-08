"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, datetime
import pathlib
from PIL import Image
from sqlalchemy.dialects.postgresql import JSONB
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                                                  ondelete="CASCADE"),
                                                  nullable=False)
    alt_text = db.Column(db.String, nullable=True)
    file_name = db.Column(db.String, nullable=False)
    file_size = db.Column(db.String, nullable=False)
    storage_name = db.Column(db.String, nullable=False)
    local_filesystem = db.Column(db.Boolean, default=True) #Remote storage = False
    user = db.relationship("User", viewonly=True)

    def __init__(self):
        Storage.__init__(self)
        self.created = datetime.datetime.now().isoformat()
        self.encrypted = False

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    @property
    def directory(self):
        return f"{current_app.config['MEDIA_DIR']}/{self.user_id}"

    def save_media(self, user, file, alt_text):
        self.user_id = user.id
        self.alt_text = alt_text
        self.file_name = file.filename
        extension = pathlib.Path(self.file_name).suffix
        self.storage_name = f"{utils.gen_random_string()}{extension}"
        saved = super().save_file(file, self.storage_name, self.directory)
        if saved:
            self.save()
            self.save_thumbnail()
        return saved

    def delete_media(self):
        Storage.__init__(self)
        removed_media = super().delete_file(self.storage_name, self.directory)
        removed_thumbnail = self.delete_thumbnail()
        self.delete()
        if removed_media and removed_thumbnail:
            return True
        return False

    def delete_thumbnail(self):
        storage_name = f"tn-{self.storage_name}"
        return super().delete_file(storage_name, self.directory)

    def _get_media_url(self, storage_name):
        if self.local_filesystem:
            host_url = self.user.site.host_url
            return f"{host_url}file/media/{self.user_id}/{storage_name}"
        else:
            """ creates a URL for the media file on the minio server """
            bucket_name = f"{self.user.site.hostname}.media"
            media_path = f"{bucket_name}/{self.user_id}/{storage_name}"
            return f"{os.environ['MINIO_URL']}/{media_path}"

    def get_url(self):
        return self._get_media_url(self.storage_name)

    def get_thumbnail_url(self):
        return self._get_media_url(f"tn-{self.storage_name}")

    def get_media(self):
        bytes = super().get_file(self.storage_name, self.directory)
        return bytes, self.file_name

    def does_media_exits(self, thumbnail=False):
        name = self.storage_name if thumbnail==False else f"tn-{self.storage_name}"
        return True if super().does_file_exist(self.directory, name) else False

    def save_thumbnail(self):
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
        storage = Storage()
        storage.save_file(tmp_thumbnail_path, storage_name, self.directory)
        #except Exception as error:
        #    current_app.logger.warning(f"Could not create thumbnail: {error}")

    def get_values(self):
        return {
                    "id": self.id,
                    "created": self.created.strftime('%Y-%m-%d'),
                    "file_name": self.file_name,
                    "file_size": self.file_size,
                    "image_url": self.get_url(),
                    "thumbnail_url": self.get_thumbnail_url(),
                    "alt_text": self.alt_text,
                }


#@event.listens_for(Media, "after_delete")
#def delete_user_media(mapper, connection, target):
#    deleted = target.delete_media()
