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

import datetime, json
from threading import Thread
from flask import g, request, render_template, redirect
from flask import session, flash, Blueprint
from flask_babel import gettext
from flask_babel import refresh as babel_refresh

from liberaforms import app
from liberaforms.models.site import Invite, Site, Installation
from liberaforms.models.user import User
from liberaforms.models.form import Form
from liberaforms.utils.wraps import *
from liberaforms.utils.utils import make_url_for, JsonResponse, logout_user
from liberaforms.utils.email import EmailServer
from liberaforms.utils import validators
import liberaforms.utils.wtf as wtf


#from pprint import pprint as pp

user_bp = Blueprint('user_bp', __name__,
                    template_folder='../templates/user')


@user_bp.route('/user/new', methods=['GET', 'POST'])
@user_bp.route('/user/new/<string:token>', methods=['GET', 'POST'])
@sanitized_token
def new_user(token=None):
    if g.site.invitationOnly and not token:
        return redirect(make_url_for('main_bp.index'))
    logout_user()
    invite=None
    if token:
        invite=Invite.find(token=token)
        if not invite:
            flash(gettext("Invitation not found"), 'warning')
            return redirect(make_url_for('main_bp.index'))
        if not validators.is_valid_token(invite.token):
            flash(gettext("This invitation has expired"), 'warning')
            invite.delete()
            return redirect(make_url_for('main_bp.index'))
    
    wtform=wtf.NewUser()
    if wtform.validate_on_submit():
        validatedEmail=False
        adminSettings=User.default_admin_settings()        
        if invite:
            if invite.email == wtform.email.data:
                validatedEmail=True
            if invite.admin == True:
                adminSettings['isAdmin']=True
                # the first admin of a new Site needs to config. SMTP before we can send emails, but
                # when validatedEmail=False, a validation email fails to be sent because SMTP is not congifured.
                if not g.site.get_admins():
                    validatedEmail=True
        if wtform.email.data in app.config['ROOT_USERS']:
            adminSettings["isAdmin"]=True
            validatedEmail=True
        
        newUserData = {
            "username": wtform.username.data,
            "email": wtform.email.data,
            "password_hash": validators.hash_password(wtform.password.data),
            "preferences": {"language": g.site.defaultLanguage, "newEntryNotification": True},
            "hostname": g.site.hostname,
            "blocked": False,
            "admin": adminSettings,
            "validatedEmail": validatedEmail,
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "token": {},
            "consentTexts": []
        }
        user = User.create(newUserData)
        if not user:
            flash(gettext("Opps! An error ocurred when creating the user"), 'error')
            return render_template('new-user.html')
        if invite:
            invite.delete()           

        thread = Thread(target=EmailServer().sendNewUserNotification(user))
        thread.start()
        
        session["user_id"]=str(user.id)
        g.current_user = user
        babel_refresh()
        flash(gettext("Welcome!"), 'success')
        
        if validatedEmail == True:
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            return redirect(make_url_for('user_bp.user_settings', username=user.username))

    if "user_id" in session:
        session.pop("user_id")
    if not wtform.email.data and invite:
        wtform.email.data = invite.email
    return render_template('new-user.html', wtform=wtform)


@user_bp.route('/user/<string:username>', methods=['GET'])
@login_required
def user_settings(username):
    if username != g.current_user.username:
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('user-settings.html', user=g.current_user)
 

@user_bp.route('/user/<string:username>/statistics', methods=['GET'])
@enabled_user_required
def statistics(username):
    if username != g.current_user.username:
        return redirect(make_url_for('user_bp.statistics', username=g.current_user.username))
    return render_template('user/statistics.html', user=g.current_user)


@user_bp.route('/user/send-validation', methods=['GET'])
@login_required
def send_validation_email():   
    g.current_user.set_token(email=g.current_user.email)
    EmailServer().sendConfirmEmail(g.current_user, g.current_user.email)
    flash(gettext("We've sent an email to %s") % g.current_user.email, 'info')
    return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    

""" Personal user settings """

@user_bp.route('/user/change-language', methods=['GET', 'POST'])
@login_required
def change_language():
    if request.method == 'POST':
        if 'language' in request.form and request.form['language'] in app.config['LANGUAGES']:
            g.current_user.preferences["language"]=request.form['language']
            g.current_user.save()
            babel_refresh()
            flash(gettext("Language updated OK"), 'success')
            return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('common/change-language.html', current_language=g.current_user.language)


@user_bp.route('/user/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    wtform=wtf.ChangeEmail()
    if wtform.validate_on_submit():
        g.current_user.set_token(email=wtform.email.data)
        EmailServer().sendConfirmEmail(g.current_user, wtform.email.data)
        flash(gettext("We've sent an email to %s") % wtform.email.data, 'info')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('change-email.html', wtform=wtform)
    

@user_bp.route('/user/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password():
    wtform=wtf.ResetPassword()
    if wtform.validate_on_submit():
        g.current_user.password_hash=validators.hash_password(wtform.password.data)
        g.current_user.save()
        flash(gettext("Password changed OK"), 'success')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('reset-password.html', wtform=wtform)


@user_bp.route('/user/delete-account/<string:user_id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_account(user_id):
    user = User.find(id=user_id)
    if not user or user.id != g.current_user.id:
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    if g.current_user.is_admin() and g.site.get_admins().count() == 1:
        flash(gettext("Cannot delete. You are the only Admin on this site"), 'warning')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    wtform=wtf.DeleteAccount()
    if wtform.validate_on_submit():
        g.current_user.delete_user()
        logout_user()
        flash(gettext("Thank you for using LiberaForms"), 'success')
        return redirect(make_url_for('main_bp.index'))
    return render_template( 'delete-account.html', wtform=wtform, user=g.current_user)


@user_bp.route('/user/toggle-new-entry-notification', methods=['POST'])
@enabled_user_required
def toggle_new_entry_notification_default():
    default=g.current_user.toggle_new_entry_notification_default()
    return JsonResponse(json.dumps({'default': default}))


"""
This may be used to validate a New user's email, or an existing user's Change email request
"""
@user_bp.route('/user/validate-email/<string:token>', methods=['GET'])
@sanitized_token
def validate_email(token):
    user = User.find(token=token)
    if not user:
        flash(gettext("We couldn't find that petition"), 'warning')
        return redirect(make_url_for('main_bp.index'))
    if not validators.is_valid_token(user.token):
        flash(gettext("Your petition has expired"), 'warning')
        user.delete_token()
        return redirect(make_url_for('main_bp.index'))
    # On a Change email request, the new email address is saved in the token.
    if 'email' in user.token:
        user.email = user.token['email']
    
    user.delete_token()
    user.validatedEmail=True
    user.save()
    #login the user
    session['user_id']=str(user.id)
    flash(gettext("Your email address is valid"), 'success')
    return redirect(make_url_for('user_bp.user_settings', username=user.username))


@user_bp.route('/user/<string:username>/consent', methods=['GET'])
@enabled_user_required
def consent(username):
    if username != g.current_user.username:
        return redirect(make_url_for('user_bp.consent', username=g.current_user.username))
    return render_template('user/consent.html')


""" Login / Logout """

@user_bp.route('/user/login', methods=['GET', 'POST'])
@anon_required
def login():
    logout_user()
    wtform=wtf.Login()
    if wtform.validate():
        user=User.find(hostname=g.site.hostname, username=wtform.username.data, blocked=False)
        if not user and validators.is_valid_email(wtform.username.data):
            user=User.find(hostname=g.site.hostname, email=wtform.username.data, blocked=False)
        if user and user.verify_password(wtform.password.data):
            session["user_id"]=str(user.id)
            if not user.validatedEmail:
                return redirect(make_url_for('user_bp.user_settings', username=user.username))
            else:
                return redirect(make_url_for('form_bp.my_forms'))
        else:
            flash(gettext("Bad credentials"), 'warning')
    return render_template('login.html', wtform=wtform)


@user_bp.route('/user/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(make_url_for('main_bp.index'))
