"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, logging, datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import event
from liberaforms.utils.database import CRUD
from liberaforms import db
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
        return cls.query.filter_by(**kwargs).first()

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


class AnswerAttachment(db.Model, CRUD):
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

    def __init__(self, answer, file):
        self.created = datetime.datetime.now().isoformat()
        self.file_name = file.filename
        self.answer_id = answer.id
        self.form_id = answer.form.id
        self.storage_name = utils.gen_random_string()
        dir = answer.form.get_attachment_dir()
        if not os.path.exists(dir):
            os.makedirs(dir)
        storage_path = os.path.join(dir, self.storage_name)
        file.save(storage_path)

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    def get_directory(self):
        return self.form.get_attachment_dir()

    def get_url(self):
        host_url = self.form.site.host_url
        form_id = self.form.id
        return f"{host_url}file/{form_id}/{self.storage_name}"


@event.listens_for(AnswerAttachment, "after_delete")
def delete_answer_attachment(mapper, connection, target):
    attachment_path = os.path.join(target.get_directory(), target.storage_name)
    if os.path.exists(attachment_path):
        os.remove(attachment_path)
    else:
        logging.warning(f"Attachment not found at: {attachment_path}")
