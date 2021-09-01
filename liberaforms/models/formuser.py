"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.ext.mutable import MutableDict
from liberaforms import db
from liberaforms.utils.database import CRUD

class FormUser(db.Model, CRUD):
    __tablename__ = "form_users"
    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    created = db.Column(TIMESTAMP, nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id',
                                                ondelete="CASCADE"),
                                                nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',
                                                ondelete="CASCADE"),
                                                nullable=False)
    is_editor = db.Column(db.Boolean, default=False)
    notifications = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    field_index = db.Column(JSONB, nullable=True)
    order_by = db.Column(db.String, nullable=True)
    user = db.relationship("User", viewonly=True)
    form = db.relationship("Form", viewonly=True)


    def __init__(self, **kwargs):
        self.created = datetime.now(timezone.utc)
        self.user_id = kwargs['user_id']
        self.form_id = kwargs['form_id']
        self.is_editor = kwargs['is_editor']
        self.notifications = kwargs['notifications']

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    def toggle_expiration_notification(self):
        preference = self.notifications['expiredForm']
        self.notifications['expiredForm'] = False if preference else True
        self.save()
        return self.notifications['expiredForm']

    def toggle_notification(self):
        preference = self.notifications['newAnswer']
        self.notifications['newAnswer'] = False if preference else True
        self.save()
        return self.notifications['newAnswer']
