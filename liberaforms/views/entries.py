"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os, json
from flask import g, render_template, redirect
from flask import session, flash
from flask import Blueprint, send_file, after_this_request
from flask_babel import gettext

from liberaforms.models.form import Form
from liberaforms.utils.wraps import *
from liberaforms.utils.utils import make_url_for

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
    csv_file=queriedForm.writeCSV(with_deleted_columns=request.args.get('with_deleted_columns'))
    
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
    print(request.json["id"])
    response = queriedForm.findEntry(request.json["id"])
    if not response:
        return json.dumps({'deleted': False})
    response.delete()
    
    queriedForm.expired = queriedForm.hasExpired()
    queriedForm.save()
    queriedForm.addLog(gettext("Deleted an entry"))
    return json.dumps({'deleted': True})


@entries_bp.route('/forms/undo-delete-entry/<string:id>', methods=['POST'])
@enabled_user_required
def undo_delete_entry(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return json.dumps({'undone': False, 'new_id': None})
    entry_data={}
    for field in request.json:
        try:
            entry_data[field["name"]]=field["value"]
        except:
            return json.dumps({'undone': False, 'new_id': None})
    entry = queriedForm.addEntry(entry_data)
    
    queriedForm.expired = queriedForm.hasExpired()
    queriedForm.save()
    queriedForm.addLog(gettext("Undeleted an entry"))
    return json.dumps({'undone': True, 'new_id': str(entry.id)})


@entries_bp.route('/forms/toggle-marked-entry/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_marked_entry(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not (queriedForm and "id" in request.json):
        return json.dumps({'marked': False})
    #print(request.json["id"])
    response = queriedForm.findEntry(request.json["id"])
    if not response:
        return json.dumps({'marked': False})
    response.marked = False if response.marked == True else True
    response.save()
    return json.dumps({'marked': response.marked})


@entries_bp.route('/forms/change-entry-field-value/<string:id>', methods=['POST'])
@enabled_user_required
def change_entry(id):
    queriedForm=Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return json.dumps({'saved': False})
        
    # get the 'created' field position
    created_pos=next((i for i,field in enumerate(request.json) if "name" in field and field["name"] == "created"), None)
    if not isinstance(created_pos, int):
        return json.dumps({'saved': False})
    foundEntries = [entry for entry in queriedForm.entries if entry['created'] == request.json[created_pos]["value"]]
    if not foundEntries or len(foundEntries) > 1:
        """ If there are two entries with the same 'created' value, we don't change anything """
        return json.dumps({'saved': False})
    try:
        entry_pos = [pos for pos, entry in enumerate(queriedForm.entries) if entry == foundEntries[0]][0]
    except:
        return json.dumps({'saved': False})
    modifiedEntry={}
    for field in request.json:
        try:
            modifiedEntry[field["name"]]=field["value"]
        except:
            return json.dumps({'saved': False})
    del queriedForm.entries[entry_pos]
    queriedForm.entries.insert(entry_pos, modifiedEntry)
    queriedForm.expired = queriedForm.hasExpired()
    queriedForm.save()
    queriedForm.addLog(gettext("Modified an entry"))
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
        if queriedForm.getTotalEntries() == totalEntries:
            queriedForm.deleteEntries()
            if not queriedForm.hasExpired() and queriedForm.expired:
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
    if not queriedForm or not queriedForm.areEntriesShared():
        return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400
    return render_template('view-results.html', form=queriedForm, language=get_locale())    


@entries_bp.route('/<string:slug>/stats/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_stats(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.areEntriesShared():
        return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400
    return render_template('chart-entries.html', form=queriedForm, shared=True)


@entries_bp.route('/<string:slug>/csv/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_csv(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.areEntriesShared():
        return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400
    csv_file = queriedForm.writeCSV()
    
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
    if not queriedForm or not queriedForm.areEntriesShared():
        return JsonResponse(json.dumps({}), 404)
    if queriedForm.restrictedAccess and not g.current_user:
        return JsonResponse(json.dumps({}), 404)
    return JsonResponse(json.dumps(queriedForm.getEntriesForJSON()))
