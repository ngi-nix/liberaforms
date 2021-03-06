"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json
import mimetypes
from flask import g, request, render_template, redirect
from flask import Blueprint, current_app
from flask import session, flash
from flask_babel import gettext as _

from liberaforms.models.site import Site
from liberaforms.models.invite import Invite
from liberaforms.models.user import User
from liberaforms.utils.wraps import *
from liberaforms.utils import utils
from liberaforms.utils.utils import make_url_for, JsonResponse
from liberaforms.utils.dispatcher import Dispatcher
import liberaforms.utils.wtf as wtf

from pprint import pprint

site_bp = Blueprint('site_bp', __name__,
                    template_folder='../templates/site')


@site_bp.route('/site/save-blurb', methods=['POST'])
@admin_required
def save_blurb():
    if 'editor' in request.form:
        g.site.save_blurb(request.form['editor'])
        flash(_("Text saved OK"), 'success')
    return redirect(make_url_for('main_bp.index'))


@site_bp.route('/site/recover-password', methods=['GET', 'POST'])
@site_bp.route('/site/recover-password/<string:token>', methods=['GET'])
@anon_required
@sanitized_token
def recover_password(token=None):
    if token:
        user = User.find(token=token)
        if not user:
            flash(_("Couldn't find that token"), 'warning')
            return redirect(make_url_for('main_bp.index'))
        if validators.has_token_expired(user.token):
            flash(_("Your petition has expired"), 'warning')
            user.delete_token()
            return redirect(make_url_for('main_bp.index'))
        if user.blocked:
            user.delete_token()
            flash(_("Your account has been blocked"), 'warning')
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
        if not user and wtform.email.data in current_app.config['ROOT_USERS']:
            if not User.find(email=wtform.email.data):
                # auto invite root user
                invite=Invite(  email=wtform.email.data,
                                message="New root user",
                                token=utils.create_token(Invite),
                                admin=True)
                invite.save()
                return redirect(make_url_for('user_bp.new_user',
                                             token=invite.token['token']))
        flash(_("We may have sent you an email"), 'info')
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
                                                _("An error occured")),
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
        flash(_("Site name changed OK"), 'success')
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
            flash(_("Language updated OK"), 'success')
            return redirect(make_url_for('admin_bp.site_admin'))
    return render_template('common/change-language.html',
                            current_language=g.site.defaultLanguage,
                            go_back_to_admin_panel=True)

@site_bp.route('/site/change-icon', methods=['GET', 'POST'])
@admin_required
def change_icon():
    if request.method == 'POST':
        if not request.files['file']:
            flash(_("Required file is missing"), 'warning')
            return render_template('change-icon.html')
        file=request.files['file']
        if "image/" in file.content_type:
            try:
                g.site.change_favicon(file)
                flash(_("Logo changed OK. Refresh with  &lt;F5&gt;"), 'success')
                return redirect(make_url_for('admin_bp.site_admin'))
            except Exception as error:
                current_app.logger.error(error)
        else:
            flash(_("An image file is required"), 'warning')
            return render_template('change-icon.html')
    return render_template('change-icon.html')


@site_bp.route('/site/reset-favicon', methods=['GET'])
@admin_required
def reset_site_favicon():
    if g.site.reset_favicon():
        flash(_("Logo reset OK. Refresh with  &lt;F5&gt;"), 'success')
    return redirect(make_url_for('admin_bp.site_admin'))


@site_bp.route('/site/edit-mimetypes', methods=['GET', 'POST'])
@admin_required
def edit_mimetypes():
    wtform=wtf.FileExtensions()
    if wtform.validate_on_submit():
        mimetypes.init()
        updated_mimetypes = {"extensions":[], "mimetypes": []}
        extensions = wtform.extensions.data.splitlines()
        for extension in extensions:
            if not extension:
                continue
            type = mimetypes.types_map[f".{extension}"]
            if not extension in updated_mimetypes["extensions"]:
                updated_mimetypes["extensions"].append(extension)
                updated_mimetypes["mimetypes"].append(type)
        g.site.mimetypes = updated_mimetypes
        g.site.save()
        flash(_("Enabled file extensions updated OK"), 'success')
        return redirect(make_url_for('admin_bp.site_admin'))
    if request.method == 'GET':
        wtform.extensions.data = '\n'.join(g.site.mimetypes['extensions'])
    return render_template('edit-mimetypes.html', wtform=wtform)


@site_bp.route('/site/toggle-invitation-only', methods=['POST'])
@admin_required
def toggle_invitation_only():
    return JsonResponse(json.dumps({'invite': g.site.toggle_invitation_only()}))

@site_bp.route('/site/toggle-newuser-uploads-default', methods=['POST'])
@admin_required
def toggle_newuser_uploads_default():
    return JsonResponse(json.dumps({'uploads': g.site.toggle_newuser_uploads_default()}))

@site_bp.route('/site/primary-color', methods=['GET', 'POST'])
@admin_required
def primary_color():
    wtform=wtf.ChangePrimaryColor()
    if request.method == 'GET':
        wtform.hex_color.data=g.site.primary_color
    if wtform.validate_on_submit():
        g.site.primary_color=wtform.hex_color.data
        g.site.save()
        flash(_("Color changed OK"), 'success')
        return redirect(make_url_for('admin_bp.site_admin'))
    return render_template('set-primary-color.html', wtform=wtform)


@site_bp.route('/site/email-branding', methods=['GET', 'POST'])
@admin_required
def email_branding():
    from liberaforms.utils.dispatcher.dispatcher import HTML_email
    wtform = wtf.EmailBranding()
    if wtform.validate_on_submit():
        if request.files['header_image']:
            g.site.change_email_header(request.files['header_image'])
        footer_text = wtform.footer_text.data
        g.site.email_footer = footer_text if footer_text else None
        flash(_("Updated OK. Refresh with &lt;F5&gt;"), 'success')
        g.site.save()
        return redirect(make_url_for('site_bp.email_branding'))
    if request.method == 'GET' and g.site.email_footer:
        wtform.footer_text.data=g.site.get_email_footer()
    return render_template('email-branding.html', wtform=wtform)


@site_bp.route('/site/reset-email-header', methods=['GET'])
@admin_required
def reset_email_header():
    if g.site.reset_email_header():
        flash(_("Reset image OK. Refresh with &lt;F5&gt;"), 'success')
    return redirect(make_url_for('site_bp.email_branding'))


@site_bp.route('/site/example-email-preview', methods=['GET'])
@admin_required
def email_preview():
    from liberaforms.utils.dispatcher import dispatcher
    return dispatcher.branding_body_preview()['html']


@site_bp.route('/site/send-email-preview', methods=['POST'])
@admin_required
def send_branding_preview():
    if 'email' in request.form:
        email = request.form['email']
        if validators.is_valid_email(email):
            status = Dispatcher().send_branding_preview(email)
            if status['email_sent'] == True:
                flash(_("Sent email OK"), 'success')
            else:
                flash(status['msg'], 'warning')
            return redirect(make_url_for('site_bp.email_branding'))
    flash(_("Email address is not valid"), 'warning')
    return redirect(make_url_for('site_bp.email_branding'))


@site_bp.route('/site/stats', methods=['GET'])
@admin_required
def stats():
    return render_template('stats.html', site=g.site)


""" ROOT_USERS functions
"""

@site_bp.route('/site/email/config', methods=['GET', 'POST'])
@rootuser_required
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
        flash(_("Confguration saved OK"), 'success')
    wtf_email=wtf.GetEmail()
    return render_template('smtp-config.html',
                            wtf_smtp=wtf_smtp,
                            wtf_email=wtf_email)


@site_bp.route('/site/email/test-config', methods=['POST'])
@rootuser_required
def test_smtp():
    wtform=wtf.GetEmail()
    if wtform.validate_on_submit():
        status = Dispatcher().send_test_email(wtform.email.data)
        if status['email_sent'] == True:
            flash(_("SMTP config works!"), 'success')
        else:
            flash(status['msg'], 'warning')
    else:
        flash("Email not valid", 'warning')
    return redirect(make_url_for('site_bp.smtp_config'))


@site_bp.route('/site/edit-host-url', methods=['GET'])
@rootuser_required
def edit_host_url():
    queriedSite=Site.find()
    return render_template('edit-host-url.html', site=queriedSite)


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
