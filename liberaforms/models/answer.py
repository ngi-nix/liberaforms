"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, logging, datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import event
from liberaforms import db
from liberaforms.utils.storage.storage import Storage
from liberaforms.utils.database import CRUD
from liberaforms.utils import utils

from pprint import pprint as pp

class Answer(db.Model, CRUD):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.DateTime, nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marked = db.Column(db.Boolean, default=False)
    data = db.Column(JSONB, nullable=False)
    form = db.relationship("Form", viewonly=True)
    attachments = db.relationship(  "AnswerAttachment",
                                    lazy='dynamic',
                                    cascade = "all, delete, delete-orphan")

    def __init__(self, form_id, author_id, data):
        self.created = datetime.datetime.now().isoformat()
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


class AnswerAttachment(db.Model, CRUD, Storage):
    __tablename__ = "answer_attachments"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.DateTime, nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id',
                                                    ondelete="CASCADE"),
                                                    nullable=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    file_name = db.Column(db.String, nullable=False)
    storage_name = db.Column(db.String, nullable=False)
    form = db.relationship("Form", viewonly=True)

    def __init__(self, answer):
        Storage.__init__(self)
        self.created = datetime.datetime.now().isoformat()
        self.answer_id = answer.id
        self.form_id = answer.form.id
        self.storage_name = utils.gen_random_string()

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
        return "forms/{}".format(self.form_id)

    def save_attachment(self, file):
        self.file_name = file.filename
        saved = super().save_file(file, self.directory, self.storage_name)
        self.save()
        return saved

    def delete_attachment(self):
        return super().delete_file(self.directory, self.storage_name)

    def get_url(self):
        host_url = self.form.site.host_url
        return f"{host_url}file/{self.form_id}/{self.storage_name}"

    def get_attachment(self):
        bytes = super().get_file(self.directory, self.storage_name)
        return bytes, self.file_name


@event.listens_for(AnswerAttachment, "after_delete")
def delete_answer_attachment(mapper, connection, target):
    deleted = target.delete_attachment()
