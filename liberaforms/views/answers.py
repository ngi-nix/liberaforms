"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json
from flask import g, request, render_template, redirect
from flask import current_app, session, flash
from flask import Blueprint, send_file, send_from_directory, after_this_request
from flask_babel import gettext as _

from liberaforms.models.form import Form
from liberaforms.models.answer import Answer, AnswerAttachment
from liberaforms.utils.wraps import *
from liberaforms.utils.utils import make_url_for, get_locale, JsonResponse

#from pprint import pprint as pp

answers_bp = Blueprint('answers_bp', __name__,
                        template_folder='../templates/answers')


@answers_bp.route('/forms/answers/<int:form_id>', methods=['GET'])
@enabled_user_required
def list_answers(form_id):
    #queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    queriedForm = g.current_user.get_form(form_id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('list-answers.html',
                            form=queriedForm,
                            with_deleted_columns=request.args.get('with_deleted_columns'),
                            edit_mode=request.args.get('edit_mode'))


@answers_bp.route('/forms/answers/stats/<int:form_id>', methods=['GET'])
@enabled_user_required
def answers_stats(form_id):
    queriedForm = g.current_user.get_form(form_id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('chart-answers.html', form=queriedForm)


@answers_bp.route('/forms/csv/<int:form_id>', methods=['GET'])
@enabled_user_required
def answers_csv(form_id):
    queriedForm = g.current_user.get_form(form_id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    csv_file=queriedForm.write_csv(with_deleted_columns=request.args.get('with_deleted_columns'))

    @after_this_request
    def remove_file(response):
        os.remove(csv_file)
        return response
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)

"""
@answers_bp.route('/forms/delete-answer/<int:form_id>', methods=['POST'])
@enabled_user_required
def delete_answer(form_id):
    queriedForm = g.current_user.get_form(form_id, is_editor=True)
    if not (queriedForm and "id" in request.json):
        return JsonResponse(json.dumps({'deleted': False}))
    answer = Answer.find(id=request.json["id"], form_id=queriedForm.id)
    if not answer:
        return JsonResponse(json.dumps({'deleted': False}))
    answer.delete()

    queriedForm.expired = queriedForm.has_expired()
    queriedForm.save()
    queriedForm.add_log(_("Deleted an answer"))
    return JsonResponse(json.dumps({'deleted': True}))
"""

"""
@answers_bp.route('/forms/toggle-marked-answer/<int:form_id>', methods=['POST'])
@enabled_user_required
def toggle_marked_answer(form_id):
    queriedForm = g.current_user.get_form(form_id)  # editors and readers
    if not (queriedForm and 'id' in request.json):
        return JsonResponse(json.dumps({'marked': False}))
    try:
        answer_id = int(request.json['id'])
        answer = Answer.find(id=answer_id, form_id=queriedForm.id)
    except:
        answer = None
    if not answer:
        return JsonResponse(json.dumps({'marked': False}))
    answer.marked = False if answer.marked == True else True
    answer.save()
    return JsonResponse(json.dumps({'marked': answer.marked}))
"""

@answers_bp.route('/forms/delete-all-answers/<int:form_id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_answers(form_id):
    queriedForm = g.current_user.get_form(form_id, is_editor=True)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        try:
            totalAnswers = int(request.form['totalAnswers'])
        except:
            flash(_("We expected a number"), 'warning')
            return render_template('delete-all-answers.html', form=queriedForm)
        if queriedForm.get_total_answers() == totalAnswers:
            queriedForm.delete_all_answers()
            queriedForm.add_log(_("Deleted all answers"))
            if not queriedForm.has_expired() and queriedForm.expired:
                queriedForm.expired=False
                queriedForm.save()
            flash(_("Deleted %s answers" % totalAnswers), 'success')
            return redirect(make_url_for('answers_bp.list_answers',
                                         form_id=queriedForm.id))
        else:
            flash(_("Number of answers does not match"), 'warning')
    return render_template('delete-all-answers.html', form=queriedForm)


@answers_bp.route('/form/<int:form_id>/attachment/<string:key>', methods=['GET'])
@enabled_user_required
@sanitized_key_required
def download_attachment(form_id, key):
    queriedForm = g.current_user.get_form(form_id)
    if not (queriedForm):
        return render_template('page-not-found.html'), 400
    attachment = AnswerAttachment.find(form_id=form_id, storage_name=key)
    if not attachment:
        return render_template('page-not-found.html'), 400
    (bytes, file_name) = attachment.get_attachment()
    try:
        return send_file(bytes,
                         attachment_filename=file_name,
                         as_attachment=True)
    except:
        current_app.logger.warning(f"Missing attachment. Answer id: {attachment.answer_id}")
        return render_template('page-not-found.html'), 404
