"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, request, jsonify
from flask_babel import gettext as _
from liberaforms.models.form import Form
from liberaforms.models.schemas.form import FormSchema
from liberaforms.models.schemas.answer import AnswerSchema
from liberaforms.utils.wraps import *


form_api_bp = Blueprint('form_api_bp', __name__)


@form_api_bp.route('/api/forms', methods=['GET'])
@enabled_user_required__json
def all_forms():
    forms = Form.find_all(editor_id=g.current_user.id)
    return jsonify(
        items=FormSchema(many=True).dump(forms),
        meta={'count': forms.count()}
    ), 200


@form_api_bp.route('/api/form/<int:form_id>/answers', methods=['GET'])
@enabled_user_required__json
def form_answers(form_id):
    form = Form.find(id=form_id, editor_id=g.current_user.id)
    if not form:
        return jsonify("Denied"), 401
    page = request.args.get('page', type=int)
    if page:
        answers = form.answers.paginate(page, 10, False).items
    else:
        answers = form.answers
    return jsonify(
        items=AnswerSchema(many=True).dump(answers),
        meta={'total': form.answers.count(),
              'field_index': form.get_field_index_for_data_display(),
        }
    ), 200
