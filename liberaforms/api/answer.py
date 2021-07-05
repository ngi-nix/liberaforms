"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, jsonify
from flask_babel import gettext as _
from liberaforms.models.answer import Answer
from liberaforms.models.schemas.answer import AnswerSchema
from liberaforms.utils.wraps import *


answer_api_bp = Blueprint('answer_api_bp', __name__)


@answer_api_bp.route('/api/answer/<int:id>/mark', methods=['POST'])
@enabled_user_required__json
def toggle_answer_mark(id):
    answer = Answer.find(id=id)
    if not (answer and str(g.current_user.id) in answer.form.editors):
        return jsonify("Denied"), 401
    answer.marked = False if answer.marked == True else True
    answer.save()
    return jsonify(marked=answer.marked), 200


@answer_api_bp.route('/api/answer/<int:id>/delete', methods=['DELETE'])
@enabled_user_required__json
def delete_answer(id):
    answer = Answer.find(id=id)
    if not answer:
        return jsonify("Not found"), 404
    form = answer.form
    if not str(g.current_user.id) in form.editors:
        return jsonify("Denied"), 401
    answer.delete()
    form.expired = form.has_expired()
    form.save()
    form.add_log(_("Deleted an answer"))
    return jsonify(deleted=True), 200
