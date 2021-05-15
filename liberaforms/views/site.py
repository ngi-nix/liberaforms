"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json
from flask import g, request, render_template, redirect
from flask import Blueprint, current_app
from flask import session, flash
from flask_babel import gettext

from liberaforms.models.site import Site
from liberaforms.models.invite import Invite
from liberaforms.models.user import User
from liberaforms.utils.wraps import *
from liberaforms.utils import utils
from liberaforms.utils.utils import make_url_for, JsonResponse
from liberaforms.utils.email.dispatcher import Dispatcher
import liberaforms.utils.wtf as wtf

#from pprint import pprint as pp

site_bp = Blueprint('site_bp', __name__,
                    template_folder='../templates/site')


@site_bp.route('/site/save-blurb', methods=['POST'])
@admin_required
def save_blurb():
    if 'editor' in request.form:
        g.site.save_blurb(request.form['editor'])
        flash(gettext("Text saved OK"), 'success')
    return redirect(make_url_for('main_bp.index'))


@site_bp.route('/site/recover-password', methods=['GET', 'POST'])
@site_bp.route('/site/recover-password/<string:token>', methods=['GET'])
@anon_required
@sanitized_token
def recover_password(token=None):
    if token:
        user = User.find(token=token)
        if not user:
            flash(gettext("Couldn't find that token"), 'warning')
            return redirect(make_url_for('main_bp.index'))
        if validators.has_token_expired(user.token):
            flash(gettext("Your petition has expired"), 'warning')
            user.delete_token()
            return redirect(make_url_for('main_bp.index'))
        if user.blocked:
            user.delete_token()
            flash(gettext("Your account has been blocked"), 'warning')
            return redirect(make_url_for('main_bp.index'))
        user.delete_token()
        user.validatedEmail=True
        user.save()
        # login the user
        session['user_id']=str(user.id)
        return redirect(make_url_for('user_bp.reset_password'))

    wtform=wtf.GetEmail()
    if wtform.validate_on_submit():
        user = User.find(email=wtform.email.data, blocked=False)
        if user:
            user.set_token()
            Dispatcher().send_account_recovery(user)
        if not user and wtform.email.data in os.environ['ROOT_USERS']:
            if not User.find(email=wtform.email.data):
                # auto invite root user
                invite=Invite(  email=wtform.email.data,
                                message="New root user",
                                token=utils.create_token(Invite),
                                admin=True)
                invite.save()
                return redirect(make_url_for('user_bp.new_user',
                                             token=invite.token['token']))
        flash(gettext("We may have sent you an email"), 'info')
        return redirect(make_url_for('main_bp.index'))
    return render_template('recover-password.html', wtform=wtform)


@site_bp.route('/site/consent-texts', methods=['GET'])
@admin_required
def consent():
    return render_template('site/consent.html', site=g.site)


@site_bp.route('/site/save-consent/<string:id>', methods=['POST'])
@admin_required
def save_consent(id):
    if 'markdown' in request.form \
        and "label" in request.form \
        and "required" in request.form:
        data = request.form.to_dict(flat=True)
        consent = g.site.save_consent(id, data=data)
        if consent:
            return JsonResponse(json.dumps(consent))
    return JsonResponse(json.dumps({'html': "<h1>%s</h1>" % (
                                                gettext("An error occured")),
                                    "label":""}))



@site_bp.route('/site/update-enabled-new-user-consentment-texts/<string:id>', methods=['POST'])
@admin_required
def updateEnabledNewUserConsentmentTexts(id):
    return JsonResponse(json.dumps({'included': g.site.update_included_new_user_consentment_texts(id)}))


@site_bp.route('/site/toggle-consent-enabled/<string:id>', methods=['POST'])
@admin_required
def toggle_consent_text(id):
    return JsonResponse(json.dumps({'enabled': g.site.toggle_consent_enabled(id)}))


@site_bp.route('/site/preview-new-user-form', methods=['GET'])
@admin_required
def preview_new_user_form():
    return render_template('new-user.html', wtform=wtf.NewUser(), preview_only=True)


@site_bp.route('/site/change-sitename', methods=['GET', 'POST'])
@admin_required
def change_siteName():
    if request.method == 'POST' and 'sitename' in request.form:
        g.site.siteName=request.form['sitename']
        g.site.save()
        flash(gettext("Site name changed OK"), 'success')
        return redirect(make_url_for('admin_bp.site_admin'))
    return render_template('change-sitename.html', site=g.site)


@site_bp.route('/site/change-default-language', methods=['GET', 'POST'])
@admin_required
def change_default_language():
    if request.method == 'POST':
        if 'language' in request.form \
            and request.form['language'] in current_app.config['LANGUAGES']:
            g.site.defaultLanguage=request.form['language']
            g.site.save()
            flash(gettext("Language updated OK"), 'success')
            return redirect(make_url_for('admin_bp.site_admin'))
    return render_template('common/change-language.html',
                            current_language=g.site.defaultLanguage,
                            go_back_to_admin_panel=True)

@site_bp.route('/site/change-icon', methods=['GET', 'POST'])
@admin_required
def change_icon():
    if request.method == 'POST':
        if not request.files['file']:
            flash(gettext("Required file is missing"), 'warning')
            return render_template('change-icon.html')
        file=request.files['file']
        if len(file.filename) > 4 and file.filename[-4:] == ".png":
            file.save(os.path.join(current_app.config['BRAND_DIR'], 'favicon.png'))
        else:
            flash(gettext("Bad file name. PNG only"), 'warning')
            return render_template('change-icon.html')
        flash(gettext("Icon changed OK. Refresh with  &lt;F5&gt;"), 'success')
        return redirect(make_url_for('admin_bp.site_admin'))
    return render_template('change-icon.html')


@site_bp.route('/site/reset-favicon', methods=['GET'])
@admin_required
def reset_site_favicon():
    if g.site.delete_favicon():
        flash(gettext("Favicon reset OK. Refresh with  &lt;F5&gt;"), 'success')
    return redirect(make_url_for('admin_bp.site_admin'))


@site_bp.route('/site/toggle-invitation-only', methods=['POST'])
@admin_required
def toggle_invitation_only():
    return JsonResponse(json.dumps({'invite': g.site.toggle_invitation_only()}))

@site_bp.route('/site/toggle-enable-attachments', methods=['POST'])
@admin_required
def toggle_attachments_enabled():
    return JsonResponse(json.dumps({'attachments': g.site.toggle_attachments_enabled()}))

@site_bp.route('/site/email/config', methods=['GET', 'POST'])
@admin_required
def smtp_config():
    wtf_smtp=wtf.smtpConfig(**g.site.smtpConfig)
    if wtf_smtp.validate_on_submit():
        if not wtf_smtp.encryption.data == "None":
            encryption = wtf_smtp.encryption.data
        else:
            encryption = ""
        config={}
        config['host'] = wtf_smtp.host.data
        config['port'] = wtf_smtp.port.data
        config['encryption'] = encryption
        config['user'] = wtf_smtp.user.data
        config['password'] = wtf_smtp.password.data
        config['noreplyAddress'] = wtf_smtp.noreplyAddress.data
        g.site.save_smtp_config(**config)
        flash(gettext("Confguration saved OK"), 'success')
    wtf_email=wtf.GetEmail()
    return render_template('smtp-config.html',
                            wtf_smtp=wtf_smtp,
                            wtf_email=wtf_email)


@site_bp.route('/site/email/test-config', methods=['POST'])
@admin_required
def test_smtp():
    wtform=wtf.GetEmail()
    if wtform.validate_on_submit():
        status = Dispatcher().send_test_email(wtform.email.data)
        if status['email_sent'] == True:
            flash(gettext("SMTP config works!"), 'success')
        else:
            flash(status['msg'], 'warning')
    else:
        flash("Email not valid", 'warning')
    return redirect(make_url_for('site_bp.smtp_config'))


@site_bp.route('/site/edit', methods=['GET'])
@rootuser_required
def edit_site():
    queriedSite=Site.find()
    return render_template('edit-site.html', site=queriedSite)

@site_bp.route('/site/change-menu-color', methods=['GET', 'POST'])
@admin_required
def menu_color():
    wtform=wtf.ChangeMenuColor()
    if request.method == 'GET':
        wtform.hex_color.data=g.site.menuColor
    if wtform.validate_on_submit():
        g.site.menuColor=wtform.hex_color.data
        g.site.save()
        flash(gettext("Color changed OK"), 'success')
        return redirect(make_url_for('admin_bp.site_admin'))
    return render_template('menu-color.html', wtform=wtform)

@site_bp.route('/site/stats', methods=['GET'])
@admin_required
def stats():
    return render_template('stats.html', site=g.site)


@site_bp.route('/site/toggle-scheme', methods=['POST'])
@rootuser_required
def toggle_site_scheme():
    return json.dumps({'scheme': g.site.toggle_scheme()})


@site_bp.route('/site/change-port/', methods=['POST'])
@site_bp.route('/site/change-port/<int:port>', methods=['POST'])
@rootuser_required
def change_site_port(port=None):
    g.site.port=port
    g.site.save()
    return json.dumps({'port': g.site.port})


@site_bp.route('/site/toggle-root-mode-enabled', methods=['POST'])
@admin_required
def toggle_enable_root():
    if not g.current_user.is_root_user():
        session["root_enabled"]=False
        return JsonResponse(json.dumps({'enabled': False}))
    if session["root_enabled"] == True:
        session["root_enabled"]=False
        flash(gettext("Root mode disabled"), 'success')
    else:
        session["root_enabled"]=True
        flash(gettext("Root mode enabled"), 'success')
    return JsonResponse(json.dumps({'enabled': session["root_enabled"]}))
