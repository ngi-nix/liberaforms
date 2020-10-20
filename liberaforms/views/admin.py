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

import json
from flask import g, request, render_template, redirect
from flask import session, flash, Blueprint
from flask_babel import gettext

from liberaforms.models.user import User
from liberaforms.models.form import Form
from liberaforms.utils.wraps import *
from liberaforms.utils.utils import make_url_for, JsonResponse
from liberaforms.utils.email import EmailServer
import liberaforms.utils.wtf as wtf

#from pprint import pprint as pp

admin_bp = Blueprint('admin_bp', __name__,
                    template_folder='../templates/admin')


""" User management """

@admin_bp.route('/admin', methods=['GET'])
@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    return render_template('list-users.html', users=User.findAll()) 


@admin_bp.route('/admin/users/<string:id>', methods=['GET'])
@admin_required
def inspect_user(id):
    user=User.find(id=id)
    if not user:
        flash(gettext("User not found"), 'warning')
        return redirect(make_url_for('admin_bp.list_users'))
    return render_template('inspect-user.html', user=user) 


@admin_bp.route('/admin/users/toggle-blocked/<string:id>', methods=['POST'])
@admin_required
def toggle_user_blocked(id):       
    user=User.find(id=id)
    if not user:
        return JsonResponse(json.dumps())
    if user.id == g.current_user.id:
        # current_user cannot disable themself
        blocked=user.blocked
    else:
        blocked=user.toggleBlocked()
    return JsonResponse(json.dumps({'blocked':blocked}))


@admin_bp.route('/admin/users/toggle-admin/<string:id>', methods=['POST'])
@admin_required
def toggle_admin(id):       
    user=User.find(id=id)
    if not user:
        return JsonResponse(json.dumps())
    if user.username == g.current_user.username:
        # current_user cannot remove their own admin permission
        isAdmin=True
    else:
        isAdmin=user.toggleAdmin()
    return JsonResponse(json.dumps({'admin':isAdmin}))


@admin_bp.route('/admin/users/delete/<string:id>', methods=['GET', 'POST'])
@admin_required
def delete_user(id):       
    user=User.find(id=id)
    if not user:
        flash(gettext("User not found"), 'warning')
        return redirect(make_url_for('admin_bp.list_users'))
  
    if request.method == 'POST' and 'username' in request.form:
        if user.isRootUser():
            flash(gettext("Cannot delete root user"), 'warning')
            return redirect(make_url_for('admin_bp.inspect_user', id=user.id)) 
        if user.id == g.current_user.id:
            flash(gettext("Cannot delete yourself"), 'warning')
            return redirect(make_url_for('admin_bp.inspect_user', username=user.username)) 
        if user.username == request.form['username']:
            user.deleteUser()
            flash(gettext("Deleted user '%s'" % (user.username)), 'success')
            return redirect(make_url_for('admin_bp.list_users'))
        else:
            flash(gettext("Username does not match"), 'warning')
    return render_template('delete-user.html', user=user)



""" Form management """

@admin_bp.route('/admin/forms', methods=['GET'])
@admin_required
def list_forms():
    return render_template('list-forms.html', forms=Form.findAll()) 


@admin_bp.route('/admin/forms/toggle-public/<string:id>', methods=['GET'])
@admin_required
def toggle_form_public_admin_prefs(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    queriedForm.toggleAdminFormPublic()
    return redirect(make_url_for('form_bp.inspect_form', id=id))


@admin_bp.route('/admin/forms/change-author/<string:id>', methods=['GET', 'POST'])
@admin_required
def change_author(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('user_bp.my_forms'))
    if request.method == 'POST':
        author = queriedForm.getAuthor()
        if not ('old_author_username' in request.form and \
                request.form['old_author_username']==author.username):
            flash(gettext("Current author incorrect"), 'warning')
            return render_template('change-author.html', form=queriedForm)
        if 'new_author_username' in request.form:
            new_author=User.find(username=request.form['new_author_username'], hostname=queriedForm.hostname)
            if new_author:
                if new_author.enabled:
                    old_author=author
                    if queriedForm.changeAuthor(new_author):
                        queriedForm.addLog(gettext("Changed author from %s to %s" % (old_author.username, new_author.username)))
                        flash(gettext("Changed author OK"), 'success')
                        return redirect(make_url_for('form_bp.inspect_form', id=queriedForm.id))
                else:
                    flash(gettext("Cannot use %s. The user is not enabled" % (request.form['new_author_username'])), 'warning')
            else:
                flash(gettext("Can't find username %s" % (request.form['new_author_username'])), 'warning')
    return render_template('change-author.html', form=queriedForm)



""" Personal Admin preferences """

@admin_bp.route('/admin/toggle-newuser-notification', methods=['POST'])
@admin_required
def toggle_newUser_notification(): 
    return json.dumps({'notify': g.current_user.toggleNewUserNotification()})


@admin_bp.route('/admin/toggle-newform-notification', methods=['POST'])
@admin_required
def toggle_newForm_notification(): 
    return json.dumps({'notify': g.current_user.toggleNewFormNotification()})
