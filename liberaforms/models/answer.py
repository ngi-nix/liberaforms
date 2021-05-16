"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, datetime
from flask import current_app
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
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
    files = db.relationship("AnswerAttachment",
                            lazy='dynamic',
                            cascade="all, delete, delete-orphan")

    def __init__(self, form_id, author_id, data, marked=False, created=None):
        if created:
            self.created = created
        else:
            self.created = datetime.datetime.now().isoformat()
        self.form_id = form_id
        self.author_id = author_id
        self.marked = marked
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
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    file_name = db.Column(db.String, nullable=False)
    storage_name = db.Column(db.String, nullable=False)
    form_field_name = db.Column(db.String, nullable=False)
    form = db.relationship("Form", viewonly=True)

    def __init__(self, answer, field_name, file):
        self.created = datetime.datetime.now().isoformat()
        self.file_name = file.filename
        self.answer_id = answer.id
        self.form_field_name = field_name
        self.form_id = answer.form.id
        self.storage_name = utils.gen_random_string()
        dir = os.path.join( current_app.config['UPLOAD_DIR'],
                            'forms',
                            str(answer.form.id))
        if not os.path.exists(dir):
            os.makedirs(dir)
        storage_path = os.path.join(dir, self.storage_name)
        file.save(storage_path)

    def __str__(self):
        return utils.print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    def get_directory(self):
        return os.path.join(current_app.config['UPLOAD_DIR'],
                            'forms',
                            str(self.form.id))

    def get_url(self):
        host_url = self.form.site.host_url
        form_id = self.form.id
        return f"{host_url}file/{form_id}/{self.storage_name}"
