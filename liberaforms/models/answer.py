"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, re
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import event, func
from flask import current_app
from liberaforms import db
from liberaforms.utils.storage.storage import Storage
from liberaforms.utils.database import CRUD
from liberaforms.utils import utils

import sqlalchemy
from sqlalchemy.sql.expression import cast

from pprint import pprint as pp

class Answer(db.Model, CRUD):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(TIMESTAMP, nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marked = db.Column(db.Boolean, default=False)
    data = db.Column(JSONB, nullable=False)
    form = db.relationship("Form", viewonly=True)
    attachments = db.relationship(  "AnswerAttachment",
                                    lazy='dynamic',
                                    cascade = "all, delete, delete-orphan")

    def __init__(self, form_id, author_id, data):
        self.created = datetime.now(timezone.utc)
        self.form_id = form_id
        self.author_id = author_id
        self.marked = False
        self.data = data

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def find_all(cls, **kwargs):
        order = cls.created.desc()
        if 'oldest_first' in kwargs:
            if kwargs['oldest_first']:
                order = cls.created
            kwargs.pop('oldest_first')
        return cls.query.filter_by(**kwargs).order_by(order)

    def update_field(self, field_name, field_value):
        self.data[field_name] = field_value
        flag_modified(self, "data")
        self.save()

    @staticmethod
    def get_file_field_url(value):
        # extract url from html <a>
        url = re.search(r'https?:[\'"]?([^\'" >]+)', value)
        return url.group(0) if url else None

class AnswerAttachment(db.Model, CRUD, Storage):
    __tablename__ = "attachments"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(TIMESTAMP, nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id',
                                                    ondelete="CASCADE"),
                                                    nullable=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    file_name = db.Column(db.String, nullable=False)
    storage_name = db.Column(db.String, nullable=False)
    local_filesystem = db.Column(db.Boolean, default=True) #Remote storage = False
    file_size = db.Column(db.Integer, nullable=False)
    encrypted = db.Column(db.Boolean, default=False)
    form = db.relationship("Form", viewonly=True)

    def __init__(self, answer):
        Storage.__init__(self)
        self.created = datetime.now(timezone.utc)
        self.answer_id = answer.id
        self.form_id = answer.form.id

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    @classmethod
    def calc_total_size(cls, author_id=None, form_id=None):
        query = cls.query
        if author_id:
            query = query.join(Answer).filter(Answer.author_id == author_id)
        elif form_id:
            query = query.filter(cls.form_id == form_id)
        total = query.with_entities(
                    func.sum(cls.file_size.cast(sqlalchemy.Integer))
                ).scalar()
        return total if total else 0

    @property
    def directory(self):
        return f"{current_app.config['ATTACHMENT_DIR']}/{self.form_id}"

    def save_attachment(self, file):
        self.file_name = file.filename
        self.storage_name = f"{utils.gen_random_string()}.{str(self.answer_id)}"
        saved = super().save_file(file, self.storage_name, self.directory)
        if saved:
            self.save()
            return True
        else:
            current_app.logger.error(f"Did not save attachment. Answer id: {self.answer_id}")
            return False

    def delete_attachment(self):
        return super().delete_file(self.storage_name, self.directory)

    def get_url(self):
        host_url = self.form.site.host_url
        return f"{host_url}form/{self.form_id}/attachment/{self.storage_name}"

    def get_attachment(self):
        bytes = super().get_file(self.storage_name, self.directory)
        return bytes, self.file_name

    def does_attachment_exist(self):
        return True if super().does_file_exist(self.directory, self.storage_name) else False


@event.listens_for(AnswerAttachment, "after_delete")
def delete_answer_attachment(mapper, connection, target):
    deleted = target.delete_attachment()
