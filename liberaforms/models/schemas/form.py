"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import ma
from liberaforms.models.form import Form


class FormSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Form

    id = ma.auto_field()
    created = ma.auto_field()
    slug = ma.auto_field()
    structure = ma.auto_field()
    introduction_md = ma.Method('get_introduction_md')

    def get_introduction_md(self, obj):
        return obj.introductionText['markdown']
