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

from pprint import pprint

form_api_bp = Blueprint('form_api_bp', __name__)


@form_api_bp.route('/api/forms/<int:user_id>', methods=['GET'])
@enabled_user_required__json
def my_forms(user_id):
    """ Return json required by vue data-table component
    """
    if not user_id == g.current_user.id:
        return jsonify("Denied"), 401
    forms = Form.find_all(editor_id=g.current_user.id)
    form_count = forms.count()
    forms = FormSchema(many=True).dump(forms)
    field_index = [ {'name': 'form__html', 'label': _('Form')},
                    {'name': 'answers__html', 'label': _('Answers')},
                    {'name': 'created', 'label': _('Created')}
                ]
    items = []
    for form in forms:
        item = {}
        data = {}
        id = form['id']
        url = form['url']
        slug = form['slug']
        total_answers = form['total_answers']
        data['form__html'] = f"<a href='/forms/view/{id}'>{slug}</a>"
        icon =f"<i class='fa fa-bar-chart' aria-label=\"{_('Statistics')}\"></i>"
        stats_link = f"<a href='/forms/answers/stats/{id}'>{icon}</a>"
        answers_link = f"<a href='/forms/answers/{id}' \
                            alt_text=\"{_('Answers')}\"> \
                            {total_answers} \
                            </a>"
        data['answers__html'] = f"{stats_link} {answers_link}"

        for key in form.keys():
            if key == 'slug' or key == 'url' or key == 'total_answers':
                continue
            if key == 'id':
                item[key] = form[key]
                continue;
            if key == 'created':
                item[key] = form[key]
                continue;
            data[key] = form[key]
        item['data'] = data
        items.append(item)
        #pprint(items)

    return jsonify(
        items=items,
        meta={'total': form_count, 'field_index': field_index}
    ), 200


@form_api_bp.route('/api/form/<int:form_id>/answers', methods=['GET'])
@enabled_user_required__json
def form_answers(form_id):
    """ Return json required by vue data-table component
    """
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
