"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import ma
#from liberaforms.models.form import Form
from liberaforms.models.answer import Answer


class AnswerSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Answer

    id = ma.Int(dump_only=True)
    created = ma.auto_field(dump_only=True)
    marked = ma.Bool()
    data = ma.auto_field()
    form = ma.auto_field()
    """
    form_id = ma.auto_field()
    author_id = ma.auto_field()
    attachments = ma.auto_field()
    """
