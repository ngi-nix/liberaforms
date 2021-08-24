"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, jsonify
from flask_babel import gettext as _
from liberaforms.models.form import Form
from liberaforms.models.answer import Answer
from liberaforms.models.schemas.answer import AnswerSchema
from liberaforms.utils.wraps import *

from pprint import pprint

answer_api_bp = Blueprint('answer_api_bp', __name__)


@answer_api_bp.route('/api/answer/<int:answer_id>/mark', methods=['POST'])
@enabled_user_required__json
def toggle_answer_mark(answer_id):
    answer = Answer.find(id=answer_id)
    if not answer:
        return jsonify("Not found"), 404
    if not str(g.current_user.id) in answer.form.editors:
        return jsonify("Forbidden"), 403
    answer.marked = False if answer.marked == True else True
    answer.save()
    return jsonify(marked=answer.marked), 200


@answer_api_bp.route('/api/answer/<int:answer_id>/delete', methods=['DELETE'])
@enabled_user_required__json
def delete_answer(answer_id):
    answer = Answer.find(id=answer_id)
    if not answer:
        return jsonify("Not found"), 404
    form = answer.form
    if not str(g.current_user.id) in form.editors:
        return jsonify("Forbidden"), 403
    answer.delete()
    form.expired = form.has_expired()
    form.save()
    form.add_log(_("Deleted an answer"))
    return jsonify(deleted=True), 200


@answer_api_bp.route('/api/form/<int:form_id>/answers/change-index', methods=['POST'])
@enabled_user_required__json
def change_answer_field_index(form_id):
    """ Changes User's Answer field index preference for this form
    """
    form = Form.find(id=form_id, editor_id=g.current_user.id)
    if not form:
        return jsonify("Not found"), 404
    field_index = form.get_editor_field_index_preference(g.current_user.id)
    if not field_index:
        field_index = form.get_field_index_for_data_display()

    data = request.get_json(silent=True)
    new_first_field_name = data['field_name']
    field_to_move = None
    for field in field_index:
        if field['name'] == new_first_field_name:
            field_to_move = field
            break
    if field_to_move:
        old_index = field_index.index(field_to_move)
        field_index.insert(1, field_index.pop(old_index))
        form.save_editor_field_index_preference(g.current_user.id, field_index)
        return jsonify(
            {'field_index': field_index}
        ), 200
    return jsonify("Not Acceptable"), 406


@answer_api_bp.route('/api/form/<int:form_id>/answers/reset-index', methods=['POST'])
@enabled_user_required__json
def reset_answers_field_index(form_id):
    """ Resets User's Answer field index preference for this form
    """
    form = Form.find(id=form_id, editor_id=g.current_user.id)
    if not form:
        return jsonify("Not found"), 404
    field_index = form.get_field_index_for_data_display()
    form.save_editor_field_index_preference(g.current_user.id, field_index)
    return jsonify(
        {'field_index': field_index}
    ), 200
