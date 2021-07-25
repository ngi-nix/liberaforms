"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import TIMESTAMP
from liberaforms import db
from liberaforms.utils.database import CRUD

class FormLog(db.Model, CRUD):
    __tablename__ = "form_logs"
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(TIMESTAMP, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    #form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id',
                                                    ondelete="CASCADE"),
                                                    nullable=True)
    message = db.Column(db.String, nullable=False)
    user = db.relationship("User", viewonly=True)
    form = db.relationship("Form", viewonly=True)

    def __init__(self, **kwargs):
        self.created = datetime.now(timezone.utc)
        self.user_id = kwargs['user_id']
        self.form_id = kwargs['form_id']
        self.message = kwargs['message']

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)
