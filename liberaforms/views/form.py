"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json, datetime
from threading import Thread
from flask import current_app, Blueprint
from flask import g, request, render_template, redirect
from flask import session, flash, send_file, after_this_request
from flask_babel import gettext

from liberaforms import csrf
from liberaforms.models.form import Form
from liberaforms.models.user import User
from liberaforms.models.answer import Answer
from liberaforms.utils.wraps import *
from liberaforms.utils import form_helper
from liberaforms.utils import sanitizers
from liberaforms.utils import validators
from liberaforms.utils.email import EmailServer
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils.utils import make_url_for, JsonResponse, logout_user
import liberaforms.utils.wtf as wtf

#from pprint import pprint as pp

form_bp = Blueprint('form_bp', __name__,
                    template_folder='../templates/form')


@form_bp.route('/forms', methods=['GET'])
@enabled_user_required
def my_forms():
    return render_template( 'my-forms.html', user=g.current_user)

"""
@form_bp.route('/forms/templates', methods=['GET'])
@login_required
def list_form_templates():
    return render_template('form_templates.html', templates=formTemplates)
"""

@form_bp.route('/forms/new', methods=['GET'])
@form_bp.route('/forms/new/<string:templateID>', methods=['GET'])
@enabled_user_required
def new_form(templateID=None):
    form_helper.clear_session_form_data()
    session['introductionTextMD'] = Form.default_introduction_text()
    return render_template('edit-form.html', host_url=g.site.host_url)


@form_bp.route('/forms/edit', methods=['GET', 'POST'])
@form_bp.route('/forms/edit/<int:id>', methods=['GET', 'POST'])
@enabled_user_required
def edit_form(id=None):
    queriedForm=None
    if id:
        if session['form_id'] != str(id):
            flash_text = gettext("Something went wrong. id does not match session['form_id']")
            flash(flash_text, 'error')
            return redirect(make_url_for('form_bp.my_forms'))
        queriedForm = Form.find(id=id, editor_id=g.current_user.id)
        if not queriedForm:
            flash(gettext("You can't edit that form"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        if queriedForm:
            session['slug'] = queriedForm.slug
        elif 'slug' in request.form:
            session['slug'] = sanitizers.sanitize_slug(request.form['slug'])
        if not session['slug']:
            flash(gettext("Something went wrong. No slug!"), 'error')
            return redirect(make_url_for('form_bp.my_forms'))
        structure = form_helper.repair_form_structure(
                                        json.loads(request.form['structure'])
                                )
        session['formStructure'] = json.dumps(structure)
        session['formFieldIndex'] = Form.create_field_index(structure)
        session['introductionTextMD'] = sanitizers.escape_markdown(
                                            request.form['introductionTextMD']
                                        )
        return redirect(make_url_for('form_bp.preview_form'))
    optionsWithData = {}
    if queriedForm:
        optionsWithData = queriedForm.get_multichoice_options_with_saved_data()
    return render_template('edit-form.html',
                            host_url=g.site.host_url,
                            multichoiceOptionsWithSavedData=optionsWithData)


@form_bp.route('/forms/check-slug-availability', methods=['POST'])
@enabled_user_required
def is_slug_available():
    if 'slug' in request.form and request.form['slug']:
        slug=request.form['slug']
    else:
        return JsonResponse(json.dumps({'slug':"", 'available':False}))
    available = True
    slug=sanitizers.sanitize_slug(slug)
    if not slug:
        available = False
    elif Form.find(slug=slug):
        available = False
    elif slug in current_app.config['RESERVED_SLUGS']:
        available = False
    # we return a sanitized slug as a suggestion for the user.
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))


@form_bp.route('/forms/preview', methods=['GET'])
@enabled_user_required
def preview_form():
    if not ('slug' in session and 'formStructure' in session):
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template( 'preview-form.html',
                            slug=session['slug'],
                            introductionText=sanitizers.markdown2HTML(
                                                session['introductionTextMD'])
                                            )

@form_bp.route('/forms/edit/conditions/<int:id>', methods=['GET'])
@enabled_user_required
def conditions_form(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    #pp(queriedForm.structure)
    return render_template('conditions.html', form=queriedForm)


@form_bp.route('/forms/save', methods=['POST'])
@form_bp.route('/forms/save/<int:id>', methods=['POST'])
@enabled_user_required
def save_form(id=None):
    if 'structure' in request.form:
        loaded_form_structure = json.loads(request.form['structure'])
        structure = form_helper.repair_form_structure(loaded_form_structure)
        session['formStructure'] = json.dumps(structure)
        session['formFieldIndex'] = Form.create_field_index(structure)
    if 'introductionTextMD' in request.form:
        md_text = sanitizers.escape_markdown(request.form['introductionTextMD'])
        session['introductionTextMD'] = md_text
    formStructure = json.loads(session['formStructure'])
    if not formStructure:
        formStructure=[{'label': gettext("Form"),
                        'subtype': 'h1',
                        'type': 'header'}]
    md_text = sanitizers.escape_markdown(session['introductionTextMD'])
    html = sanitizers.markdown2HTML(session['introductionTextMD'])
    introductionText={  'markdown': md_text,
                        'html': html}

    queriedForm = Form.find(id=id, editor_id=g.current_user.id) if id else None
    if queriedForm:
        queriedForm.structure=formStructure
        queriedForm.update_field_index(session['formFieldIndex'])
        queriedForm.update_expiryConditions()
        queriedForm.introductionText=introductionText
        queriedForm.save()
        form_helper.clear_session_form_data()
        flash(gettext("Updated form OK"), 'success')
        queriedForm.add_log(gettext("Form edited"))
        return redirect(make_url_for('form_bp.inspect_form', id=queriedForm.id))
    else:
        # this is a new form
        if not session['slug']:
            flash(gettext("Slug is missing."), 'error')
            return redirect(make_url_for('form_bp.edit_form'))
        if Form.find(slug=session['slug']):
            flash(gettext("Slug is not unique. %s" % (session['slug'])), 'error')
            return redirect(make_url_for('form_bp.edit_form'))
        if session['duplication_in_progress']:
            # this new form is a duplicate
            consentTexts=session['consentTexts']
            afterSubmitText=session['afterSubmitText']
            expiredText=session['expiredText']
        else:
            consentTexts=[Form.new_data_consent()]
            afterSubmitText={'html':"", 'markdown':""}
            expiredText={'html':"", 'markdown':""}
        #pp(formStructure)
        new_form_data={
                        "slug": session['slug'],
                        "structure": formStructure,
                        "fieldIndex": session['formFieldIndex'],
                        "introductionText": introductionText,
                        "consentTexts": consentTexts,
                        "afterSubmitText": afterSubmitText,
                        "expiredText": expiredText
                    }
        try:
            new_form = Form(g.current_user, **new_form_data)
            new_form.save()
        except:
            flash(gettext("Failed to save form"), 'error')
            return redirect(make_url_for('form_bp.edit_form'))
        form_helper.clear_session_form_data()
        new_form.add_log(gettext("Form created"))
        flash(gettext("Saved form OK"), 'success')
        # notify admins
        thread = Thread(target=EmailServer().sendNewFormNotification(new_form))
        thread.start()
        return redirect(make_url_for('form_bp.inspect_form', id=new_form.id))


@form_bp.route('/forms/save-consent/<int:form_id>/<string:consent_id>', methods=['POST'])
@enabled_user_required
def save_data_consent(form_id, consent_id):
    queriedForm = Form.find(id=form_id, editor_id=g.current_user.id)
    if not queriedForm:
        pay_load = {'html': "Info: Queried form not found",
                    'markdown': "", "label": ""}
        return JsonResponse(json.dumps(pay_load))
    if  "markdown" in request.form and \
        "label" in request.form and \
        "required" in request.form:
        consent = queriedForm.save_consent( consent_id,
                                            data=request.form.to_dict(flat=True)
                                            )
        if consent:
            return JsonResponse(json.dumps(consent))
    pay_load = {'html': "<h1>%s</h1>" % gettext("An error occured"),"label":""}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/forms/default-consent/<int:form_id>/<string:consent_id>', methods=['GET'])
@enabled_user_required
def default_consent_text(form_id, consent_id):
    queriedForm = Form.find(id=form_id, editor_id=g.current_user.id)
    if queriedForm:
        pay_load = json.dumps(g.site.get_consent_for_display(consent_id))
        return JsonResponse(pay_load)
    pay_load = {'html': "<h1>%s</h1>" % gettext("An error occured"),"label":""}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/forms/save-after-submit-text/<int:id>', methods=['POST'])
@enabled_user_required
def save_after_submit_text(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps({'html': "", 'markdown': ""}))
    if 'markdown' in request.form:
        queriedForm.save_after_submit_text(request.form['markdown'])
        pay_load = {'html':queriedForm.after_submit_text_html,
                    'markdown': queriedForm.after_submit_text_markdown}
        return JsonResponse(json.dumps(pay_load))
    pay_load = {'html': "<h1>%s</h1>" % gettext("An error occured"),
                'markdown': ""}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/forms/save-expired-text/<int:id>', methods=['POST'])
@enabled_user_required
def save_expired_text(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps({'html': "", 'markdown': ""}))
    if 'markdown' in request.form:
        queriedForm.save_expired_text(request.form['markdown'])
        pay_load = {'html': queriedForm.expired_text_html,
                    'markdown': queriedForm.expired_text_markdown}
        return JsonResponse(json.dumps(pay_load))
    pay_load = {'html': "<h1>%s</h1>" % gettext("An error occured"),
                'markdown': ""}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/forms/delete/<int:id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_form(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        if queriedForm.slug == request.form['slug']:
            entry_cnt = queriedForm.get_entries().count()
            queriedForm.delete_form()
            flash_text = gettext("Deleted '%s' and %s entries" % (
                                                        queriedForm.slug,
                                                        entry_cnt))
            flash(flash_text, 'success')
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            flash(gettext("Form name does not match"), 'warning')
    return render_template('delete-form.html', form=queriedForm)


@form_bp.route('/forms/view/<int:id>', methods=['GET'])
@enabled_user_required
def inspect_form(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if not g.current_user.can_inspect_form(queriedForm):
        flash(gettext("Permission needed to view form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    # prepare the session for possible form edit
    form_helper.populate_session_with_form(queriedForm)
    return render_template('inspect-form.html', form=queriedForm)


@form_bp.route('/forms/share/<int:id>', methods=['GET'])
@enabled_user_required
def share_form(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('share-form.html',
                            form=queriedForm,
                            wtform=wtf.GetEmail())


@form_bp.route('/forms/add-editor/<int:id>', methods=['POST'])
@enabled_user_required
def add_editor(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    wtform=wtf.GetEmail()
    if wtform.validate():
        newEditor=User.find(email=wtform.email.data)
        if not newEditor or newEditor.enabled==False:
            flash(gettext("Can't find a user with that email"), 'warning')
            return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))
        if str(newEditor.id) in queriedForm.editors:
            flash(gettext("%s is already an editor" % newEditor.email), 'warning')
            return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))

        if queriedForm.add_editor(newEditor):
            flash(gettext("New editor added ok"), 'success')
            queriedForm.add_log(gettext("Added editor %s" % newEditor.email))
    return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))


@form_bp.route('/forms/remove-editor/<int:form_id>/<string:editor_id>', methods=['POST'])
@enabled_user_required
def remove_editor(form_id, editor_id):
    queriedForm = Form.find(id=form_id, editor_id=g.current_user.id)
    editor = User.find(id=editor_id)
    if queriedForm and editor and not queriedForm.is_author(editor):
        queriedForm.remove_editor(editor)
        queriedForm.add_log(gettext("Removed editor %s" % editor.email))
        return json.dumps(str(editor.id))
    return json.dumps(False)


@form_bp.route('/forms/expiration/<int:id>', methods=['GET'])
@enabled_user_required
def expiration(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('expiration.html', form=queriedForm)


@form_bp.route('/forms/set-expiration-date/<int:id>', methods=['POST'])
@enabled_user_required
def set_expiration_date(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    if 'date' in request.form and 'time' in request.form:
        if request.form['date'] and request.form['time']:
            expireDate="%s %s:00" % (request.form['date'], request.form['time'])
            if not validators.is_valid_date(expireDate):
                pay_load = {'error': gettext("Date-time is not valid"),
                            'expired': queriedForm.has_expired()}
                return JsonResponse(json.dumps(pay_load))
            else:
                queriedForm.save_expiry_date(expireDate)
                queriedForm.add_log(gettext("Expiry date set to: %s" % expireDate))
        elif not request.form['date'] and not request.form['time']:
            if queriedForm.expiryConditions['expireDate']:
                queriedForm.save_expiry_date(False)
                queriedForm.add_log(gettext("Expiry date cancelled"))
        else:
            pay_load = {'error': gettext("Missing date or time"),
                        'expired': queriedForm.has_expired()}
            return JsonResponse(json.dumps(pay_load))
        return JsonResponse(json.dumps({'expired': queriedForm.has_expired()}))


@form_bp.route('/forms/set-expiry-field-condition/<int:id>', methods=['POST'])
@enabled_user_required
def set_expiry_field_condition(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps({'condition': False}))
    if 'field_name' in request.form and 'condition' in request.form:
        condition=queriedForm.save_expiry_field_condition(
                                                    request.form['field_name'],
                                                    request.form['condition'])
        field_label = queriedForm.get_field_label(request.form['field_name'])
        queriedForm.add_log(gettext("Field '%s' expiry set to: %s" % (
                                                    field_label,
                                                    request.form['condition']))
                                    )
        return JsonResponse(json.dumps({'condition': condition,
                                        'expired': queriedForm.expired}))
    return JsonResponse(json.dumps({'condition': False}))


@form_bp.route('/forms/set-expiry-total-entries/<int:id>', methods=['POST'])
@enabled_user_required
def set_expiry_total_entries(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps({'expired': False, 'total_entries':0}))
    if 'total_entries' in request.form:
        try:
            total_entries = int(request.form['total_entries'])
            if total_entries < 0:
                total_entries = 0
            queriedForm.save_expiry_total_entries(total_entries)
        except:
            total_entries = queriedForm.expiryConditions['totalEntries']
            return JsonResponse(json.dumps({'expired': False,
                                            'total_entries': total_entries,
                                            "error": True}))
    total_entries = queriedForm.expiryConditions['totalEntries']
    return JsonResponse(json.dumps({'expired': queriedForm.expired,
                                    'total_entries':total_entries}))


@form_bp.route('/forms/duplicate/<int:id>', methods=['GET'])
@enabled_user_required
def duplicate_form(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    form_helper.populate_session_with_form(queriedForm)
    session['slug']=""
    session['form_id']=None
    session['duplication_in_progress'] = True
    flash(gettext("You can edit the duplicate now"), 'info')
    return render_template('edit-form.html', host_url=g.site.host_url)


@form_bp.route('/forms/log/list/<int:id>', methods=['GET'])
@enabled_user_required
def list_log(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('list-log.html', form=queriedForm)



""" Form settings """

@form_bp.route('/form/toggle-enabled/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_form_enabled(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    enabled=queriedForm.toggle_enabled()
    queriedForm.add_log(gettext("Public set to: %s" % enabled))
    return JsonResponse(json.dumps({'enabled': enabled}))


@form_bp.route('/form/toggle-shared-entries/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_shared_entries(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    shared=queriedForm.toggle_shared_entries()
    queriedForm.add_log(gettext("Shared entries set to: %s" % shared))
    return JsonResponse(json.dumps({'enabled':shared}))


@form_bp.route('/form/toggle-restricted-access/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_restricted_access(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    access=queriedForm.toggle_restricted_access()
    queriedForm.add_log(gettext("Restricted access set to: %s" % access))
    return JsonResponse(json.dumps({'restricted':access}))


@form_bp.route('/form/toggle-notification/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_form_notification(id):
    editor_id=g.current_user.id
    queriedForm = Form.find(id=id, editor_id=editor_id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    pay_load = {'notification':queriedForm.toggle_notification(editor_id)}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/form/toggle-data-consent/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_form_dataconsent(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    dataConsentBool=queriedForm.toggle_data_consent_enabled()
    queriedForm.add_log(gettext("Data protection consent set to: %s" % dataConsentBool))
    return JsonResponse(json.dumps({'enabled':dataConsentBool}))


@form_bp.route('/form/toggle-send-confirmation/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_form_sendconfirmation(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    sendConfirmationBool=queriedForm.toggle_send_confirmation()
    queriedForm.add_log(gettext("Send Confirmation set to: %s" % sendConfirmationBool))
    return JsonResponse(json.dumps({'confirmation':sendConfirmationBool}))


@form_bp.route('/form/toggle-expiration-notification/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_form_expiration_notification(id):
    editor_id=g.current_user.id
    queriedForm = Form.find(id=id, editor_id=editor_id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    return JsonResponse(json.dumps({
            'notification':queriedForm.toggle_expiration_notification(editor_id)
        }))


@form_bp.route('/embed/<string:slug>', methods=['GET', 'POST'])
@csrf.exempt
@sanitized_slug_required
def view_embedded_form(slug):
    logout_user()
    g.embedded=True
    return view_form(slug=slug)

@form_bp.route('/<string:slug>', methods=['GET', 'POST'])
@sanitized_slug_required
def view_form(slug):
    queriedForm = Form.find(slug=slug)
    if not queriedForm:
        if g.current_user:
            flash(gettext("Can't find that form"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            return render_template('page-not-found.html'), 400
    if not queriedForm.is_public():
        if g.current_user:
            if queriedForm.expired:
                flash(gettext("That form has expired"), 'warning')
            else:
                flash(gettext("That form is not public"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
        if queriedForm.expired:
            return render_template('form-has-expired.html',
                                    form=queriedForm,
                                    navbar=False, no_bot=True), 400
        else:
            return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400

    if request.method == 'POST':
        formData=request.form.to_dict(flat=False)
        entry = {'marked': False}
        for key in formData:
            if key=='csrf_token':
                continue
            value = formData[key]
            if isinstance(value, list): # A checkboxes-group contains multiple values
                value=', '.join(value) # convert list of values to a string
                key=key.rstrip('[]') # remove tailing '[]' from the name attrib (appended by formbuilder)
            value=sanitizers.remove_first_and_last_newlines(value.strip())
            entry[key]=value
        new_answer = Answer(queriedForm.id, queriedForm.author_id, entry)
        new_answer.save()

        if not queriedForm.expired and queriedForm.has_expired():
            queriedForm.expired=True
            emails=[]
            for editor_id, preferences in queriedForm.editors.items():
                if preferences["notification"]["expiredForm"]:
                    user=User.find(id=editor_id)
                    if user and user.enabled:
                        emails.append(user.email)
            if emails:
                def sendExpiredFormNotification():
                    EmailServer().sendExpiredFormNotification(emails, queriedForm)
                thread = Thread(target=sendExpiredFormNotification())
                thread.start()
        queriedForm.save()

        if queriedForm.might_send_confirmation_email() and \
            'send-confirmation' in formData:
            confirmationEmail=queriedForm.get_confirmation_email_address(entry)
            if confirmationEmail and validators.is_valid_email(confirmationEmail):
                def sendConfirmation():
                    EmailServer().sendConfirmation(confirmationEmail, queriedForm)
                thread = Thread(target=sendConfirmation())
                thread.start()

        emails=[]
        for editor_id, preferences in queriedForm.editors.items():
            if preferences["notification"]["newEntry"]:
                user=User.find(id=editor_id)
                if user and user.enabled:
                    emails.append(user.email)
        if emails:
            def sendEntryNotification():
                data=[]
                for field in queriedForm.get_field_index_for_data_display():
                    if field['name'] in entry:
                        if field['name']=="marked":
                            continue
                        data.append( (field['label'], entry[field['name']]) )
                EmailServer().sendNewFormEntryNotification( emails,
                                                            data,
                                                            queriedForm.slug)
            thread = Thread(target=sendEntryNotification())
            thread.start()
        return render_template('thankyou.html', form=queriedForm, navbar=False)
    return render_template('view-form.html', form=queriedForm,
                                             navbar=False,
                                             no_bot=True)
