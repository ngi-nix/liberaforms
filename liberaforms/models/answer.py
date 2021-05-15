"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, datetime
from flask import current_app
from sqlalchemy.dialects.postgresql import JSONB
from liberaforms.utils.database import CRUD
from liberaforms import db
from liberaforms.utils import utils

#from pprint import pprint

class Answer(db.Model, CRUD):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.DateTime, nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marked = db.Column(db.Boolean, default=False)
    data = db.Column(JSONB, nullable=False)
    form = db.relationship("Form", viewonly=True)
    files = db.relationship("AnswerUpload",
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

    @classmethod
    def undo_delete(cls, form_id, user_id, data):
        if not (data and 'created' in data and 'marked' in data):
            return None
        created = data['created']
        data.pop('created')
        marked = data['marked']
        data.pop('marked')
        recovered_answer = cls( form_id,
                                user_id,
                                data,
                                marked=marked,
                                created=created)
        try:
            recovered_answer.save()
            return recovered_answer
        except:
            return None


class AnswerUpload(db.Model, CRUD):
    __tablename__ = "answer_uploads"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(db.DateTime, nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=False)
    file_name = db.Column(db.String, nullable=False)
    storage_name = db.Column(db.String, nullable=False)
    answer = db.relationship("Answer", viewonly=True)

    def __init__(self, answer, file):
        self.created = datetime.datetime.now().isoformat()
        self.file_name = file.filename
        self.answer_id = answer.id
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

    def get_file_path(self):
        return os.path.join(current_app.config['UPLOAD_DIR'],
                            'forms',
                            str(self.answer.form.id),
                            self.storage_name)

    def get_download_url(self):
        host_url = self.answer.form.site.host_url
        form_id = self.answer.form.id
        return f"{host_url}file/{form_id}/{self.storage_name}"
