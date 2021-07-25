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

<<<<<<< HEAD
    id = ma.Int(dump_only=True)
    created = ma.auto_field()
    slug = ma.auto_field()
=======
    id = ma.auto_field()
    created = ma.auto_field()
    slug = ma.auto_field()
    url = ma.Method('get_url')
    structure = ma.auto_field()
    introduction_md = ma.Method('get_introduction_md')

    def get_url(self, obj):
        return obj.url

    def get_introduction_md(self, obj):
        return obj.introductionText['markdown']
>>>>>>> develop
