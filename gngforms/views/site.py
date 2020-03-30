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

import os
from flask import g, render_template, redirect, request
from flask import session, flash
from flask import Blueprint, send_file, after_this_request
from flask_babel import gettext

from gngforms import app
from gngforms.models import *
from gngforms.utils.wraps import *
from gngforms.utils.utils import *
import gngforms.utils.wtf as wtf
import gngforms.utils.email as smtp

site_bp = Blueprint('site_bp', __name__,
                    template_folder='../templates/site')


@site_bp.route('/site/save-blurb', methods=['POST'])
@admin_required
def save_blurb():
    if 'editor' in request.form:            
        g.site.saveBlurb(request.form['editor'])
        flash(gettext("Text saved OK"), 'success')
    return redirect(make_url_for('main_bp.index'))


@site_bp.route('/site/save-personal-data-consent-text', methods=['POST'])
@admin_required
def save_data_consent():
    if 'editor' in request.form:            
        g.site.savePersonalDataConsentText(request.form['editor'])
        flash(gettext("Text saved OK"), 'success')
    return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))


@site_bp.route('/site/change-sitename', methods=['GET', 'POST'])
@admin_required
def change_siteName():
    if request.method == 'POST' and 'sitename' in request.form:
        g.site.siteName=request.form['sitename']
        g.site.save()
        flash(gettext("Site name changed OK"), 'success')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('change-sitename.html', site=g.site)


@site_bp.route('/site/change-favicon', methods=['GET', 'POST'])
@admin_required
def change_site_favicon():
    if request.method == 'POST':
        if not request.files['file']:
            flash(gettext("Required file is missing"), 'warning')
            return render_template('change-site-favicon.html')
        file=request.files['file']
        # need to lower filename
        if len(file.filename) > 4 and file.filename[-4:] == ".png":
            filename="%s_favicon.png" % g.site.hostname
            file.save(os.path.join(app.config['FAVICON_FOLDER'], filename))
        else:
            flash(gettext("Bad file name. PNG only"), 'warning')
            return render_template('change-site-favicon.html')
        flash(gettext("Favicon changed OK. Refresh with  &lt;F5&gt;"), 'success')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    return render_template('change-site-favicon.html')


@site_bp.route('/site/reset-favicon', methods=['GET'])
@admin_required
def reset_site_favicon():
    if g.site.deleteFavicon():
        flash(gettext("Favicon reset OK. Refresh with  &lt;F5&gt;"), 'success')
    return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))


@site_bp.route('/admin/toggle-invitation-only', methods=['POST'])
@admin_required
def toggle_invitation_only(): 
    return json.dumps({'invite': g.site.toggleInvitationOnly()})


@site_bp.route('/site/email/config', methods=['GET', 'POST'])
@admin_required
def smtp_config():
    wtf_smtp=wtf.smtpConfig(**g.site.smtpConfig)
    if wtf_smtp.validate_on_submit():
        config={}
        config['host'] = wtf_smtp.host.data
        config['port'] = wtf_smtp.port.data
        config['encryption']=wtf_smtp.encryption.data if not wtf_smtp.encryption.data=="None" else ""
        config['user'] = wtf_smtp.user.data
        config['password'] = wtf_smtp.password.data
        config['noreplyAddress'] = wtf_smtp.noreplyAddress.data
        g.site.saveSMTPconfig(**config)
        flash(gettext("Confguration saved OK"), 'success')
    wtf_email=wtf.GetEmail()
    return render_template('smtp-config.html', wtf_smtp=wtf_smtp, wtf_email=wtf_email)


@site_bp.route('/site/email/test-config', methods=['POST'])
@admin_required
def test_smtp():
    wtform=wtf.GetEmail()
    if wtform.validate():
        if smtp.sendTestEmail(wtform.email.data):
            flash(gettext("SMTP config works!"), 'success')
    else:
        flash("Email not valid", 'warning')
    return redirect(make_url_for('site_bp.smtp_config'))


@site_bp.route('/update', methods=['GET', 'POST'])
@site_bp.route('/site/update', methods=['GET', 'POST'])
def schema_update():
    installation=Installation.get()
    if installation.isSchemaUpToDate():
        if g.current_user:
            flash(gettext("Schema is already up to date. Nothing to do."), 'info')
            return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
        else:
            return render_template('page-not-found.html'), 400
    if request.method == 'POST':
        if 'secret_key' in request.form and request.form['secret_key'] == app.config['SECRET_KEY']:
            installation.updateSchema()
            flash(gettext("Updated schema OK!"), 'success')
            if g.current_user:
                return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
            else:
                return redirect(make_url_for('main_bp.index'))
        else:
            flash("Wrong secret", 'warning')
    return render_template('schema-upgrade.html', installation=installation)
    

@site_bp.route('/admin/sites/edit/<string:hostname>', methods=['GET'])
@rootuser_required
def edit_site(hostname):
    queriedSite=Site.find(hostname=hostname)
    return render_template('edit-site.html', site=queriedSite)


@site_bp.route('/admin/sites/toggle-scheme/<string:hostname>', methods=['POST'])
@rootuser_required
def toggle_site_scheme(hostname): 
    queriedSite=Site.find(hostname=hostname)
    return json.dumps({'scheme': queriedSite.toggleScheme()})


@site_bp.route('/admin/sites/change-port/<string:hostname>/', methods=['POST'])
@site_bp.route('/admin/sites/change-port/<string:hostname>/<string:port>', methods=['POST'])
@rootuser_required
def change_site_port(hostname, port=None):
    queriedSite=Site.find(hostname=hostname)
    if not port:
        queriedSite.port=None
    else:
        try:
            int(port)
            queriedSite.port=port
        except:
            pass
    queriedSite.save()
    return json.dumps({'port': queriedSite.port})
    

@site_bp.route('/admin/sites/delete/<string:hostname>', methods=['GET', 'POST'])
@rootuser_required
def delete_site(hostname):
    queriedSite=Site.find(hostname=hostname)
    if not queriedSite:
        flash(gettext("Site not found"), 'warning')
        return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
    if request.method == 'POST' and 'hostname' in request.form:
        if queriedSite.hostname == request.form['hostname']:
            if g.site.hostname == queriedSite.hostname:
                flash(gettext("Cannot delete current site"), 'warning')
                return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))
            queriedSite.deleteSite()
            flash(gettext("Deleted %s" % (queriedSite.host_url)), 'success')
            return redirect(make_url_for('user_bp.user_settings', username=g.current_user.username))       
        else:
            flash(gettext("Site name does not match"), 'warning')
    return render_template('delete-site.html', site=queriedSite)
