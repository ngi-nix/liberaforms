"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import db

class CRUD():
    def save(self):
        if self.id == None:
            db.session.add(self)
        return db.session.commit()

    def delete(self):
        db.session.delete(self)
        return db.session.commit()

def create_tables():
    from liberaforms.models.site import Site
    from liberaforms.models.user import User
    from liberaforms.models.form import Form
    from liberaforms.models.answer import Answer
    from liberaforms.models.invite import Invite
    from liberaforms.models.log import FormLog
    db.create_all()
