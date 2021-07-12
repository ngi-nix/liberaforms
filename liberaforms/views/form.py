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
from flask_babel import gettext as _

from liberaforms import csrf
from liberaforms.models.form import Form
from liberaforms.models.user import User
from liberaforms.models.answer import Answer, AnswerAttachment
from liberaforms.models.media import Media
from liberaforms.form_templates import form_templates
from liberaforms.utils.wraps import *
from liberaforms.utils import form_helper
from liberaforms.utils import sanitizers
from liberaforms.utils import validators
from liberaforms.utils.dispatcher.dispatcher import Dispatcher
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils.utils import (make_url_for, JsonResponse,
                                     logout_user, human_readable_bytes)
import liberaforms.utils.wtf as wtf

#from pprint import pprint

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
    return redirect(make_url_for('form_bp.edit_form'))


@form_bp.route('/forms/edit', methods=['GET', 'POST'])
@form_bp.route('/forms/edit/<int:form_id>', methods=['GET', 'POST'])
@enabled_user_required
def edit_form(form_id=None):
    queriedForm=None
    if form_id:
        if session['form_id'] != str(form_id):
            flash_text = _("Something went wrong. id does not match session['form_id']")
            flash(flash_text, 'error')
            return redirect(make_url_for('form_bp.my_forms'))
        queriedForm = Form.find(id=form_id, editor_id=g.current_user.id)
        if not queriedForm:
            flash(_("You can't edit that form"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        if queriedForm:
            session['slug'] = queriedForm.slug
        elif 'slug' in request.form:
            session['slug'] = sanitizers.sanitize_slug(request.form['slug'])
            if not form_helper.is_slug_available(session['slug']):
                flash(_("Something went wrong. Slug not unique!"), 'error')
                return redirect(make_url_for('form_bp.edit_form'))
        if not session['slug']:
            flash(_("Something went wrong. No slug!"), 'error')
            return redirect(make_url_for('form_bp.my_forms'))

        #if form_id and not form_helper.is_slug_available(session['slug']):
        #    flash(gettext("Something went wrong. slug is not unique."), 'error')
        #    return redirect(make_url_for('form_bp.edit_form'))
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
    disabled_fields = current_app.config['FORMBUILDER_DISABLED_FIELDS']
    max_media_size=human_readable_bytes(current_app.config['MAX_MEDIA_SIZE'])
    return render_template('edit-form.html',
                            host_url=g.site.host_url,
                            multichoiceOptionsWithSavedData=optionsWithData,
                            upload_media_form=wtf.UploadMedia(),
                            max_media_size_for_humans=max_media_size,)


@form_bp.route('/forms/check-slug-availability', methods=['POST'])
@enabled_user_required
def is_slug_available():
    if 'slug' in request.form and request.form['slug']:
        slug=request.form['slug']
    else:
        return JsonResponse(json.dumps({'slug':"", 'available':False}))
    available = True
    slug=sanitizers.sanitize_slug(slug)
    if not (slug and form_helper.is_slug_available(slug)):
        return JsonResponse(json.dumps({'slug':slug, 'available': False}))
    # we return a sanitized slug as a suggestion for the user.
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))


@form_bp.route('/forms/preview', methods=['GET'])
@enabled_user_required
def preview_form():
    if not ('slug' in session and 'formStructure' in session):
        return redirect(make_url_for('form_bp.my_forms'))
    max_attach_size=human_readable_bytes(current_app.config['MAX_ATTACHMENT_SIZE'])
    return render_template( 'preview-form.html',
                            slug=session['slug'],
                            introductionText=sanitizers.markdown2HTML(
                                                session['introductionTextMD']
                            ),
                            max_attachment_size_for_humans=max_attach_size,
                        )

@form_bp.route('/forms/edit/conditions/<int:id>', methods=['GET'])
@enabled_user_required
def conditions_form(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    #pprint(queriedForm.structure)
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
        formStructure=[{'label': _("Form"),
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
        flash(_("Updated form OK"), 'success')
        queriedForm.add_log(_("Form edited"))
        return redirect(make_url_for('form_bp.inspect_form', id=queriedForm.id))
    else:
        # this is a new form
        if not session['slug']:
            flash(_("Slug is missing."), 'error')
            return redirect(make_url_for('form_bp.edit_form'))
        if not form_helper.is_slug_available(session['slug']):
            # TRANSLATION: Slug is not available. <a_word>
            flash(_("Slug is not available. %s" % (session['slug'])), 'error')
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
        #pprint(formStructure)
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
            flash(_("Failed to save form"), 'error')
            return redirect(make_url_for('form_bp.edit_form'))
        form_helper.clear_session_form_data()
        new_form.add_log(_("Form created"))
        flash(_("Saved form OK"), 'success')
        # notify admins
        Dispatcher().send_new_form_notification(new_form)
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
            queriedForm.add_log(_("Edited GDPR text"))
            return JsonResponse(json.dumps(consent))
    pay_load = {'html': "<h1>%s</h1>" % _("An error occured"),"label":""}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/forms/default-consent/<int:form_id>/<string:consent_id>', methods=['GET'])
@enabled_user_required
def default_consent_text(form_id, consent_id):
    queriedForm = Form.find(id=form_id, editor_id=g.current_user.id)
    if queriedForm:
        pay_load = json.dumps(g.site.get_consent_for_display(consent_id))
        return JsonResponse(pay_load)
    pay_load = {'html': "<h1>%s</h1>" % _("An error occured"),"label":""}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/forms/save-after-submit-text/<int:id>', methods=['POST'])
@enabled_user_required
def save_after_submit_text(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps({'html': "", 'markdown': ""}))
    if 'markdown' in request.form:
        queriedForm.save_after_submit_text(request.form['markdown'])
        queriedForm.add_log(_("Edited Thankyou text"))
        pay_load = {'html':queriedForm.after_submit_text_html,
                    'markdown': queriedForm.after_submit_text_markdown}
        return JsonResponse(json.dumps(pay_load))
    pay_load = {'html': "<h1>%s</h1>" % _("An error occured"),
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
        queriedForm.add_log(_("Edited expiry text"))
        pay_load = {'html': queriedForm.expired_text_html,
                    'markdown': queriedForm.expired_text_markdown}
        return JsonResponse(json.dumps(pay_load))
    pay_load = {'html': "<h1>%s</h1>" % _("An error occured"),
                'markdown': ""}
    return JsonResponse(json.dumps(pay_load))


@form_bp.route('/forms/delete/<int:id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_form(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        if queriedForm.slug == request.form['slug']:
            answer_cnt = queriedForm.get_answers().count()
            queriedForm.delete()
            flash_text = _("Deleted '%s' and %s answers" % (
                                                        queriedForm.slug,
                                                        answer_cnt))
            flash(flash_text, 'success')
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            flash(_("Form name does not match"), 'warning')
    return render_template('delete-form.html', form=queriedForm)


@form_bp.route('/forms/view/<int:id>', methods=['GET'])
@enabled_user_required
def inspect_form(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if not g.current_user.can_inspect_form(queriedForm):
        flash(_("Permission needed to view form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    # prepare the session for possible form edit
    #pprint(queriedForm.structure)
    form_helper.populate_session_with_form(queriedForm)
    max_attach_size=human_readable_bytes(current_app.config['MAX_ATTACHMENT_SIZE'])
    return render_template('inspect-form.html',
                            form=queriedForm,
                            max_attachment_size_for_humans=max_attach_size)


@form_bp.route('/form/<int:id>/fediverse-publish', methods=['GET', 'POST'])
@enabled_user_required
def fedi_publish(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if not g.current_user.fedi_auth:
        flash(_("Fediverse connect is not configured"), 'warning')
        return redirect(make_url_for('form_bp.inspect_form', id=id))
    if request.method == 'POST':
        Dispatcher().publish_form(queriedForm, fediverse=True)
        flash(_(f"Published on {g.current_user.fedi_auth['node_url']}"), 'success')
        return redirect(make_url_for('form_bp.inspect_form', id=id))

    return render_template('fedi-publish.html', form=queriedForm)


@form_bp.route('/forms/share/<int:id>', methods=['GET'])
@enabled_user_required
def share_form(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('share-form.html',
                            form=queriedForm,
                            wtform=wtf.GetEmail())


@form_bp.route('/forms/add-editor/<int:id>', methods=['POST'])
@enabled_user_required
def add_editor(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    wtform=wtf.GetEmail()
    if wtform.validate_on_submit():
        newEditor=User.find(email=wtform.email.data)
        if not newEditor or newEditor.enabled==False:
            flash(_("Can't find a user with that email"), 'warning')
            return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))
        if str(newEditor.id) in queriedForm.editors:
            flash(_("%s is already an editor" % newEditor.email), 'warning')
            return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))

        if queriedForm.add_editor(newEditor):
            flash(_("New editor added ok"), 'success')
            queriedForm.add_log(_("Added editor %s" % newEditor.email))
    return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))


@form_bp.route('/forms/remove-editor/<int:form_id>/<string:editor_id>', methods=['POST'])
@enabled_user_required
def remove_editor(form_id, editor_id):
    queriedForm = Form.find(id=form_id, editor_id=g.current_user.id)
    editor = User.find(id=editor_id)
    if queriedForm and editor and not queriedForm.is_author(editor):
        queriedForm.remove_editor(editor)
        queriedForm.add_log(_("Removed editor %s" % editor.email))
        return json.dumps(str(editor.id))
    return JsonResponse(json.dumps(False))


@form_bp.route('/forms/add-shared-notification/<int:id>', methods=['POST'])
@enabled_user_required
def add_shared_notification(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    wtform=wtf.GetEmail()
    if request.method == 'POST':
        if wtform.validate():
            email = wtform.email.data
            if not wtform.email.data in queriedForm.shared_notifications:
                queriedForm.shared_notifications.append(email)
                log_msg = _("Added shared notification: %s" % email)
                queriedForm.add_log(log_msg)
                queriedForm.save()
    return redirect(make_url_for('form_bp.share_form',
                                 id=queriedForm.id,
                                 _anchor='notifications'))


@form_bp.route('/forms/remove-shared-notification/<int:id>', methods=['POST'])
@enabled_user_required
def remove_shared_notification(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not (queriedForm and 'email' in request.form):
        return JsonResponse(json.dumps(False))
    email = request.form.get('email')
    if not validators.is_valid_email(email):
        return JsonResponse(json.dumps(False))
    if email in queriedForm.shared_notifications:
        queriedForm.shared_notifications.remove(email)
        queriedForm.add_log(_("Removed shared notification: %s" % email))
        queriedForm.save()
        return JsonResponse(json.dumps(True))
    return JsonResponse(json.dumps(False))


@form_bp.route('/forms/expiration/<int:id>', methods=['GET'])
@enabled_user_required
def expiration(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
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
                pay_load = {'error': _("Date-time is not valid"),
                            'expired': queriedForm.has_expired()}
                return JsonResponse(json.dumps(pay_load))
            else:
                queriedForm.save_expiry_date(expireDate)
                queriedForm.add_log(_("Expiry date set to: %s" % expireDate))
        elif not request.form['date'] and not request.form['time']:
            if queriedForm.expiryConditions['expireDate']:
                queriedForm.save_expiry_date(False)
                queriedForm.add_log(_("Expiry date cancelled"))
        else:
            pay_load = {'error': _("Missing date or time"),
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
        queriedForm.add_log(_("Field '%s' expiry set to: %s" % (
                                                    field_label,
                                                    request.form['condition']))
                                    )
        return JsonResponse(json.dumps({'condition': condition,
                                        'expired': queriedForm.expired}))
    return JsonResponse(json.dumps({'condition': False}))


@form_bp.route('/forms/set-expiry-total-answers/<int:id>', methods=['POST'])
@enabled_user_required
def set_expiry_total_answers(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not (queriedForm and 'total_answers' in request.form):
        return JsonResponse(json.dumps({'expired': False, 'total_answers':0}))
    total_answers = request.form['total_answers']
    total_answers = queriedForm.save_expiry_total_answers(total_answers)
    # i18n: Expire when total answers set to: 3
    queriedForm.add_log(_("Expire when total answers set to: %s" % total_answers))
    return JsonResponse(json.dumps({'expired': queriedForm.expired,
                                    'total_answers': total_answers}))


@form_bp.route('/forms/duplicate/<int:id>', methods=['GET'])
@enabled_user_required
def duplicate_form(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    form_helper.populate_session_with_form(queriedForm)
    session['slug']=""
    session['form_id']=None
    session['duplication_in_progress'] = True
    flash(_("You can edit the duplicate now"), 'info')
    return redirect(make_url_for('form_bp.edit_form'))


@form_bp.route('/forms/log/list/<int:id>', methods=['GET'])
@enabled_user_required
def list_log(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        flash(_("Can't find that form"), 'warning')
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
    queriedForm.add_log(_("Public set to: %s" % enabled))
    return JsonResponse(json.dumps({'enabled': enabled}))


@form_bp.route('/form/toggle-shared-answers/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_shared_answers(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    shared=queriedForm.toggle_shared_answers()
    queriedForm.add_log(_("Shared answers set to: %s" % shared))
    return JsonResponse(json.dumps({'enabled':shared}))


@form_bp.route('/form/toggle-restricted-access/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_restricted_access(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    access=queriedForm.toggle_restricted_access()
    queriedForm.add_log(_("Restricted access set to: %s" % access))
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
    queriedForm.add_log(_("Data protection consent set to: %s" % dataConsentBool))
    return JsonResponse(json.dumps({'enabled':dataConsentBool}))


@form_bp.route('/form/toggle-send-confirmation/<int:id>', methods=['POST'])
@enabled_user_required
def toggle_form_sendconfirmation(id):
    queriedForm = Form.find(id=id, editor_id=g.current_user.id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    sendConfirmationBool=queriedForm.toggle_send_confirmation()
    queriedForm.add_log(_("Send Confirmation set to: %s" % sendConfirmationBool))
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
            flash(_("Can't find that form"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            return render_template('page-not-found.html'), 404
    if not queriedForm.is_public():
        if g.current_user:
            if queriedForm.expired:
                flash(_("That form has expired"), 'warning')
            else:
                flash(_("That form is not public"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
        if queriedForm.expired:
            return render_template('form-has-expired.html',
                                    form=queriedForm,
                                    navbar=False, no_bot=True), 200
        else:
            return render_template('page-not-found.html'), 404
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 404

    if request.method == 'POST':
        formData=request.form.to_dict(flat=False)
        answer_data = {'marked': False}
        for key in formData:
            if key=='csrf_token':
                continue
            value = formData[key]
            if isinstance(value, list): # A checkboxes-group contains multiple values
                value=', '.join(value) # convert list of values to a string
                key=key.rstrip('[]') # remove tailing '[]' from the name attrib (appended by formbuilder)
            value=sanitizers.remove_first_and_last_newlines(value.strip())
            answer_data[key]=value
        answer = Answer(queriedForm.id, queriedForm.author_id, answer_data)
        answer.save()

        if request.files:
            for file_field_name in request.files.keys():
                if not queriedForm.has_field(file_field_name):
                    continue
                file = request.files[file_field_name]
                # TODO: check size and mimetype
                if file.filename:
                    attachment = AnswerAttachment(answer)
                    try:
                        saved = attachment.save_attachment(file)
                        if saved:
                            url = attachment.get_url()
                            link = f'<a href="{url}">{file.filename}</a>'
                            answer.update_field(file_field_name, link)
                    except Exception as error:
                        current_app.logger.error(error)
                        err = "Failed to save attachment: form:{}, answer:{}" \
                              .format(queriedForm.slug, answer.id)
                        current_app.logger.error(err)

        if not queriedForm.expired and queriedForm.has_expired():
            queriedForm.expired=True
            queriedForm.save()
            emails=[]
            for editor_id, preferences in queriedForm.editors.items():
                if preferences["notification"]["expiredForm"]:
                    user=User.find(id=editor_id)
                    if user and user.enabled:
                        emails.append(user.email)
            emails = list(set(emails + queriedForm.shared_notifications))
            if emails:
                Dispatcher().send_expired_form_notification(emails, queriedForm)

        if queriedForm.might_send_confirmation_email() and \
            'send-confirmation' in formData:
            email=queriedForm.get_confirmation_email_address(answer)
            if email and validators.is_valid_email(email):
                Dispatcher().send_answer_confirmation(email, queriedForm)

        emails=[]
        for editor_id, preferences in queriedForm.editors.items():
            if preferences["notification"]["newAnswer"] == True:
                user=User.find(id=editor_id)
                if user and user.enabled:
                    emails.append(user.email)
        emails = list(set(emails + queriedForm.shared_notifications))
        if emails:
            data=[]
            for field in queriedForm.get_field_index_for_data_display():
                if field['name'] in answer.data:
                    if field['name']=="marked":
                        continue
                    data.append( (field['label'], answer.data[field['name']]) )
            Dispatcher().send_new_answer_notification(  emails,
                                                        data,
                                                        queriedForm.slug)
        return render_template('thankyou.html',
                                form=queriedForm,
                                navbar=False)
    max_attach_size=human_readable_bytes(current_app.config['MAX_ATTACHMENT_SIZE'])
    return render_template('view-form.html',
                            form=queriedForm,
                            max_attachment_size_for_humans=max_attach_size,
                            navbar=False,
                            no_bot=True)


@form_bp.route('/forms/templates', methods=['GET'])
@enabled_user_required
def list_templates():
    return render_template('list-templates.html',
                            templates = form_templates.templates)

@form_bp.route('/forms/template/<int:template_id>', methods=['GET'])
@enabled_user_required
def view_template(template_id):
    form_helper.clear_session_form_data()
    template = next((sub for sub in form_templates.templates if sub['id'] == template_id), None)
    if not template:
        return redirect(make_url_for('form_bp.list_templates'))
    introduction_text = sanitizers.markdown2HTML(str(template['introduction_md']))
    session['formStructure'] = template['structure']
    return render_template('preview-form.html',
                            is_template=True,
                            slug=template['name'],
                            introductionText=introduction_text,
                            template = template)

@form_bp.route('/forms/template/<int:template_id>/create-form', methods=['GET'])
@enabled_user_required
def create_form_from_template(template_id):
    form_helper.clear_session_form_data()
    template = next((sub for sub in form_templates.templates if sub['id'] == template_id), None)
    if not template:
        return redirect(make_url_for('form_bp.list_templates'))
    session['introductionTextMD']=template['introduction_md']
    session['formStructure'] = template['structure']
    flash(_("Copied template OK. You can edit your new form"), 'success')
    return redirect(make_url_for('form_bp.edit_form'))
