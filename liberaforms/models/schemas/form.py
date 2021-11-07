"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import ma
from liberaforms.models.form import Form
from liberaforms.models.formuser import FormUser
from liberaforms.models.answer import AnswerAttachment
from liberaforms.utils import utils


class FormSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Form

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

class FormSchemaForMyFormsDataDisplay(ma.SQLAlchemySchema):
    class Meta:
        model = Form

    id = ma.auto_field()
    created = ma.auto_field()
    slug = ma.auto_field()
    total_answers = ma.Method('get_total_answers')
    last_answer_date = ma.Method('get_last_answer_date')
    is_public = ma.Method('get_is_public')
    is_shared = ma.Method('get_is_shared')
    attachments_usage = ma.Method('get_attachment_usage')
    edit_mode = ma.auto_field()

    def get_total_answers(self, obj):
        return obj.answers.count()

    def get_last_answer_date(self, obj):
        return obj.get_last_answer_date()

    def get_is_public(self, obj):
        return obj.is_public()

    def get_is_shared(self, obj):
        return True if obj.users.count() > 1 else False

    def get_attachment_usage(self, obj):
        if obj.has_file_field():
            return AnswerAttachment.calc_total_size(form_id=obj.id)
        return None


class FormSchemaForAdminFormsDataDisplay(ma.SQLAlchemySchema):
    class Meta:
        model = Form

    id = ma.auto_field()
    created = ma.auto_field()
    slug = ma.auto_field()
    author_id = ma.auto_field()
    total_answers = ma.Method('get_total_answers')
    total_users = ma.Method('get_total_formusers')
    last_answer_date = ma.Method('get_last_answer_date')
    is_public = ma.Method('get_is_public')
    author = ma.Method('get_author')

    def get_total_answers(self, obj):
        return obj.answers.count()

    def get_total_formusers(self, obj):
        return FormUser.find_all(form_id=obj.id).count()

    def get_last_answer_date(self, obj):
        return obj.get_last_answer_date()

    def get_is_public(self, obj):
        return obj.is_public()

    def get_is_shared(self, obj):
        return True if obj.users.count() > 0 else False

    def get_author(self, obj):
        return {'id': obj.author.id, 'name': obj.author.username}
