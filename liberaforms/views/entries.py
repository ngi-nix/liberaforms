"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json
from flask import g, request, render_template, redirect
from flask import session, flash
from flask import Blueprint, send_file, after_this_request
from flask_babel import gettext

from liberaforms.models.form import Form, FormResponse
from liberaforms.utils.wraps import *
from liberaforms.utils.utils import make_url_for, get_locale, JsonResponse

#from pprint import pprint as pp

entries_bp = Blueprint('entries_bp', __name__,
                    template_folder='../templates/entries')
    
""" Form entries """

@entries_bp.route('/forms/entries/<string:id>', methods=['GET'])
@enabled_user_required
def list_entries(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('list-entries.html',
                            form=queriedForm,
                            with_deleted_columns=request.args.get('with_deleted_columns'),
                            edit_mode=request.args.get('edit_mode'))


@entries_bp.route('/forms/entries/stats/<string:id>', methods=['GET'])
@enabled_user_required
def entry_stats(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('chart-entries.html', form=queriedForm)


@entries_bp.route('/forms/csv/<string:id>', methods=['GET'])
@enabled_user_required
def csv_form(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    csv_file=queriedForm.write_csv(with_deleted_columns=request.args.get('with_deleted_columns'))
    
    @after_this_request 
    def remove_file(response): 
        os.remove(csv_file) 
        return response
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)


@entries_bp.route('/forms/delete-entry/<string:id>', methods=['POST'])
@enabled_user_required
def delete_entry(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not (queriedForm and "id" in request.json):
        return json.dumps({'deleted': False})
    response = queriedForm.find_entry(request.json["id"])
    if not response:
        return json.dumps({'deleted': False})
    response.delete()
    
    queriedForm.expired = queriedForm.has_expired()
    queriedForm.save()
    queriedForm.add_log(gettext("Deleted an entry"))
    return json.dumps({'deleted': True})


@entries_bp.route('/forms/undo-delete-entry/<string:id>', methods=['POST'])
@enabled_user_required
def undo_delete_entry(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return json.dumps({'undone': False, 'new_id': None})
    entry_data={}
    for field in request.json:
        entry_data[field["name"]]=field["value"]
    entry = queriedForm.add_entry(entry_data)
    queriedForm.expired = queriedForm.has_expired()
    queriedForm.save()
    queriedForm.add_log(gettext("Undeleted an entry"))
    return json.dumps({'undone': True, 'new_id': str(entry.id)})


@entries_bp.route('/forms/toggle-marked-entry/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_marked_entry(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not (queriedForm and 'id' in request.json):
        return json.dumps({'marked': False})
    response = queriedForm.find_entry(request.json["id"])
    if not response:
        return json.dumps({'marked': False})
    response.marked = False if response.marked == True else True
    response.save()
    return json.dumps({'marked': response.marked})


@entries_bp.route('/forms/change-entry-field-value/<string:id>', methods=['POST'])
@enabled_user_required
def change_entry(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not (queriedForm and 'id' in request.json):
        return json.dumps({'saved': False})
    response = queriedForm.find_entry(request.json['id'])
    if not response:
        return json.dumps({'saved': False})
    response.data = {}
    for field in request.json['data']:
        if field['name'] == 'marked' or field['name'] == 'created':
            continue
        response.data[field['name']] = field['value']
    response.save()
    queriedForm.expired = queriedForm.has_expired()
    queriedForm.save()
    queriedForm.add_log(gettext("Modified an entry"))
    return json.dumps({'saved': True})    
    

@entries_bp.route('/forms/delete-entries/<string:id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_entries(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        try:
            totalEntries = int(request.form['totalEntries'])
        except:
            flash(gettext("We expected a number"), 'warning')
            return render_template('delete-entries.html', form=queriedForm)
        if queriedForm.get_total_entries() == totalEntries:
            queriedForm.delete_entries()
            if not queriedForm.has_expired() and queriedForm.expired:
                queriedForm.expired=False
                queriedForm.save()
            flash(gettext("Deleted %s entries" % totalEntries), 'success')
            return redirect(make_url_for('entries_bp.list_entries', id=queriedForm.id))
        else:
            flash(gettext("Number of entries does not match"), 'warning')
    return render_template('delete-entries.html', form=queriedForm)


@entries_bp.route('/<string:slug>/results/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_entries(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.are_entries_shared():
        return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400
    return render_template('view-results.html', form=queriedForm, language=get_locale())    


@entries_bp.route('/<string:slug>/stats/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_stats(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.are_entries_shared():
        return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400
    return render_template('chart-entries.html', form=queriedForm, shared=True)


@entries_bp.route('/<string:slug>/csv/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_csv(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.are_entries_shared():
        return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400
    csv_file = queriedForm.write_csv()
    
    @after_this_request 
    def remove_file(response): 
        os.remove(csv_file) 
        return response
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)


@entries_bp.route('/<string:slug>/json/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_json(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.are_entries_shared():
        return JsonResponse(json.dumps({}), 404)
    if queriedForm.restrictedAccess and not g.current_user:
        return JsonResponse(json.dumps({}), 404)
    return JsonResponse(json.dumps(queriedForm.get_entries_for_json()))
