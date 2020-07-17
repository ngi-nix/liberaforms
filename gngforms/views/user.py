"""
“Copyright 2020 La Coordinadora d’Entitats per la Lleialtat Santsenca”

This file is part of GNGforms.

GNGforms is free software: you can redistribute it and/or modify
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

from flask import g, render_template, redirect
from flask import session, flash, Blueprint
from flask_babel import gettext, refresh
from threading import Thread

from gngforms import app
from gngforms.models import *
from gngforms.utils.wraps import *
from gngforms.utils.utils import *
import gngforms.utils.wtf as wtf
import gngforms.utils.email as smtp

#from pprint import pprint as pp

user_bp = Blueprint('user_bp', __name__,
                    template_folder='../templates/user')


@user_bp.route('/user/new', methods=['GET', 'POST'])
@user_bp.route('/user/new/<string:token>', methods=['GET', 'POST'])
@sanitized_token
def new_user(token=None):
    if g.site.invitationOnly and not token:
        return redirect(make_url_for('main_bp.index'))

    invite=None
    if token:
        invite=Invite.find(token=token)
        if not invite:
            flash(gettext("Invitation not found"), 'warning')
            return redirect(make_url_for('main_bp.index'))
        if not isValidToken(invite.token):
            flash(gettext("This invitation has expired"), 'warning')
            invite.delete()
            return redirect(make_url_for('main_bp.index'))
    
    wtform=wtf.NewUser()
    if wtform.validate_on_submit():
        validatedEmail=False
        adminSettings=User.defaultAdminSettings()        
        if invite:
            if invite.email == wtform.email.data:
                validatedEmail=True
            if invite.admin == True:
                adminSettings['isAdmin']=True
                # the first admin of a new Site needs to config. SMTP before we can send emails.
                # when validatedEmail=False, a validation email fails to be sent because SMTP is not congifured.
                if not g.site.admins:
                    validatedEmail=True
        if wtform.email.data in app.config['ROOT_USERS']:
            adminSettings["isAdmin"]=True
            validatedEmail=True
        
        newUserData = {
            "username": wtform.username.data,
            "email": wtform.email.data,
            "password_hash": hashPassword(wtform.password.data),
            "preferences": {"language": g.site.defaultLanguage, "newEntryNotification": True},
            "hostname": g.site.hostname,
            "blocked": False,
            "admin": adminSettings,
            "validatedEmail": validatedEmail,
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "token": {}
        }
        user = User.create(newUserData)
        if not user:
            flash(gettext("Opps! An error ocurred when creating the user"), 'error')
            return render_template('new-user.html')
        if invite:
            invite.delete()           

        thread = Thread(target=smtp.sendNewUserNotification(user))
        thread.start()
        
        if validatedEmail == True:
            # login an invited user
            session["user_id"]=str(user.id)
            flash(gettext("Welcome!"), 'success')
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            user.setToken()
            smtp.sendConfirmEmail(user)
            return render_template('new-user.html', site=g.site, created=True)

    if "user_id" in session:
        session.pop("user_id")
    return render_template('new-user.html', wtform=wtform)


@user_bp.route('/user/<string:username>', methods=['GET'])
@login_required
def user_settings(username):
    if username != g.current_user.username:
        return redirect(make_url_for('form_bp.my_forms'))
    user=g.current_user
    invites=[]
    if user.isAdmin():
        invites=Invite.findAll()
    sites=None
    installation=None
    if user.isRootUser():
        sites=Site.findAll()
        installation=Installation.get()
    context = {
        'user': user,
        'invites': invites,
        'site': g.site,
        'sites': sites,
        'installation': installation
    }
    return render_template('user-settings.html', **context)
 

@user_bp.route('/user/send-validation', methods=['GET'])
@login_required
def send_validation_email():   
    g.current_user.setToken(email=g.current_user.email)
    smtp.sendConfirmEmail(g.current_user, g.current_user.email)
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
            refresh()
            flash(gettext("Language updated OK"), 'success')
            return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('common/change-language.html', current_language=g.current_user.language)


@user_bp.route('/user/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    wtform=wtf.ChangeEmail()
    if wtform.validate_on_submit():
        g.current_user.setToken(email=wtform.email.data)
        smtp.sendConfirmEmail(g.current_user, wtform.email.data)
        flash(gettext("We've sent an email to %s") % wtform.email.data, 'info')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('change-email.html', wtform=wtform)
    

@user_bp.route('/user/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password():
    wtform=wtf.ResetPassword()
    if wtform.validate_on_submit():
        g.current_user.password_hash=hashPassword(wtform.password.data)
        g.current_user.save()
        flash(gettext("Password changed OK"), 'success')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('reset-password.html', wtform=wtform)


@user_bp.route('/site/recover-password', methods=['GET', 'POST'])
@user_bp.route('/site/recover-password/<string:token>', methods=['GET'])
@anon_required
@sanitized_token
def recover_password(token=None):
    if token:
        user = User.find(token=token)
        if not user:
            flash(gettext("Couldn't find that token"), 'warning')
            return redirect(make_url_for('main_bp.index'))
        if not isValidToken(user.token):
            flash(gettext("Your petition has expired"), 'warning')
            user.deleteToken()
            return redirect(make_url_for('main_bp.index'))
        if user.blocked:
            user.deleteToken()
            flash(gettext("Your account has been blocked"), 'warning')
            return redirect(make_url_for('main_bp.index'))
        user.deleteToken()
        user.validatedEmail=True
        user.save()
        # login the user
        session['user_id']=str(user.id)
        return redirect(make_url_for('user_bp.reset_password'))
    
    wtform=wtf.GetEmail()
    if wtform.validate_on_submit():
        user = User.find(email=wtform.email.data, blocked=False)
        if user:
            user.setToken()
            smtp.sendRecoverPassword(user)
        if not user and wtform.email.data in app.config['ROOT_USERS']:
            # root_user emails are only good for one account, across all sites.
            if not Installation.isUser(wtform.email.data):
                # auto invite root users
                message="New root user at %s." % g.site.hostname
                invite=Invite.create(g.site.hostname, wtform.email.data, message, True)
                return redirect(make_url_for('user_bp.new_user', token=invite.token['token']))
        flash(gettext("We may have sent you an email"), 'info')
        return redirect(make_url_for('main_bp.index'))
    return render_template('recover-password.html', wtform=wtform)

@user_bp.route('/user/toggle-new-entry-notification', methods=['POST'])
@enabled_user_required
def toggle_new_entry_notification_default():
    default=g.current_user.toggleNewEntryNotificationDefault()
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
    if not isValidToken(user.token):
        flash(gettext("Your petition has expired"), 'warning')
        user.deleteToken()
        return redirect(make_url_for('main_bp.index'))
    # On a Change email request, the new email address is saved in the token.
    if 'email' in user.token:
        user.email = user.token['email']
    
    user.deleteToken()
    user.validatedEmail=True
    user.save()
    #login the user
    session['user_id']=str(user.id)
    flash(gettext("Your email address is valid"), 'success')
    return redirect(make_url_for('user_bp.user_settings', username=user.username))


""" Login / Logout """

@user_bp.route('/user/login', methods=['POST'])
@anon_required
def login():
    wtform=wtf.Login()
    if wtform.validate():
        user=User.find(hostname=g.site.hostname, username=wtform.username.data, blocked=False)
        if user and user.verifyPassword(wtform.password.data):
            session["user_id"]=str(user.id)
            if not user.validatedEmail:
                return redirect(make_url_for('user_bp.user_settings', username=user.username))
            else:
                return redirect(make_url_for('form_bp.my_forms'))
    if "user_id" in session:
        session.pop("user_id")
    flash(gettext("Bad credentials"), 'warning')
    return redirect(make_url_for('main_bp.index'))


@user_bp.route('/user/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.pop("user_id")
    return redirect(make_url_for('main_bp.index'))
