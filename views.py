"""
“Copyright 2019 La Coordinadora d’Entitats per la Lleialtat Santsenca”

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

import json, re, os, datetime
from flask import request, g, Response, render_template, redirect, url_for, session, flash, send_file, after_this_request
from flask_wtf.csrf import CSRFError
from GNGforms import app, db, babel
from threading import Thread
from flask_babel import gettext, refresh
from GNGforms.persistence import *
from GNGforms.session import *
from GNGforms.utils import *
from GNGforms.email import *
from form_templates import formTemplates

import pprint


def make_url_for(function, **kwargs):
    kwargs["_external"]=True
    kwargs["_scheme"]=g.site.scheme
    return url_for(function, **kwargs)


@app.route('/test', methods=['GET'])
def test():
    #sites=Site.objects(hostname=urlparse(request.host_url).hostname)
    sites=Site.objects
    for site in sites:
        print(site.id)
       # print (site.get_obj_values_as_dict())
       
    users=User.objects
    for user in users:
        print (user.get_obj_values_as_dict())
        
    forms=Form.objects
    for form in forms:
        pprint.pprint (form.get_obj_values_as_dict())
        
    form=Form.find(id='5e638385174b6f10dd39bf46')
    pprint.pprint (form.get_obj_values_as_dict())
    form.enabled=True
    pprint.pprint(form.structure[0])
    form.save()
    return render_template('test.html', sites=sites)


@app.before_request
def before_request():    
    g.current_user=None
    g.isRootUser=False
    g.isAdmin=False
    g.site=Site.objects(hostname=urlparse(request.host_url).hostname).first()
    if '/static' in request.path:
        return

    if 'user_id' in session:
        g.current_user=User.objects(id=session["user_id"], hostname=g.site.hostname).first()
        if not g.current_user:
            session.pop("user_id")
            return
        #print(g.current_user.get_obj_values_as_dict())
        if g.current_user and g.current_user.isRootUser():
            g.isRootUser=True
        if g.current_user and g.current_user.isAdmin():
            g.isAdmin=True


@babel.localeselector
def get_locale():
    if g.current_user:
        return g.current_user.language
    else:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page-not-found.html'), 400

@app.errorhandler(500)
def server_error(error):
    return render_template('server-error.html'), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash(e.description, 'error')
    return redirect(make_url_for('index'))

@app.route('/', methods=['GET'])
def index():    
    return render_template('index.html',site=g.site)

@app.route('/<string:slug>', methods=['GET', 'POST'])
@sanitized_slug_required
def view_form(slug):
    queriedForm = Form.objects(slug=slug).first()
    if not queriedForm:
        if g.current_user:
            flash(gettext("Can't find that form"), 'warning')
            return redirect(make_url_for('my_forms'))
        return render_template('page-not-found.html'), 400
    if not queriedForm.isPublic():
        if g.current_user:
            if queriedForm.expired:
                flash(gettext("That form has expired"), 'warning')
            else:
                flash(gettext("That form is not public"), 'warning')
            return redirect(make_url_for('my_forms'))
        if queriedForm.expired:
            return render_template('form-has-expired.html'), 400
        else:
            return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400

    if request.method == 'POST':  
        formData=request.form.to_dict(flat=False)
        entry = {}
        entry["created"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for key in formData:
            if key=='csrf_token':
                continue
            value = formData[key]
            if isinstance(value, list): # A checkboxes-group contains multiple values 
                value=', '.join(value) # convert list of values to a string
                key=key.rstrip('[]') # remove tailing '[]' from the name attrib (appended by formbuilder)
            entry[key]=value
        
        queriedForm.entries.append(entry)
        
        if not queriedForm.expired and queriedForm.hasExpired():
            queriedForm.expired=True
            emails=[]
            for editor_id, preferences in queriedForm.editors.items():
                if preferences["notification"]["expiredForm"]:
                    user=User(_id=editor_id)
                    if user and user.enabled:
                        emails.append(user.email)
            if emails:
                def sendExpiredFormNotification():
                    smtpSendExpiredFormNotification(emails, queriedForm)
                thread = Thread(target=sendExpiredFormNotification())
                thread.start()
        queriedForm.save()
            
        emails=[]
        for editor_id, preferences in queriedForm.editors.items():
            if preferences["notification"]["newEntry"]:
                user=User(_id=editor_id)
                if user and user.enabled:
                    emails.append(user.email)
        if emails:
            def sendEntryNotification():
                data=[]
                for field in queriedForm.fieldIndex:
                    if field['name'] in entry:
                        data.append( (stripHTMLTagsForLabel(field['label']), entry[field['name']]) )
                smtpSendNewFormEntryNotification(emails, data, queriedForm.slug)
            thread = Thread(target=sendEntryNotification())
            thread.start()
        return render_template('thankyou.html', form=queriedForm)
    return render_template('view-form.html', form=queriedForm)     


@app.route('/<string:slug>/results/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_entries(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.areEntriesShared():
        return render_template('page-not-found.html'), 400

    return render_template('view-results.html', form=queriedForm,
                                                fieldIndex=queriedForm.getFieldIndexForDataDisplay(),
                                                language=get_locale())    


@app.route('/<string:slug>/csv/<string:key>', methods=['GET'])
@sanitized_slug_required
@sanitized_key_required
def view_csv(slug, key):
    queriedForm = Form.find(slug=slug, key=key)
    if not queriedForm or not queriedForm.areEntriesShared():
        return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400
    csv_file = writeCSV(queriedForm)
    
    @after_this_request 
    def remove_file(response): 
        os.remove(csv_file) 
        return response
    
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)


""" Editor form management """

@app.route('/forms', methods=['GET'])
@enabled_user_required
def my_forms():
    forms=Form.findAll(editor=str(g.current_user.id))
    return render_template('my-forms.html', forms=forms) 


@app.route('/forms/view/<string:id>', methods=['GET'])
@enabled_user_required
def inspect_form(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(gettext("No form found"), 'warning')
        return redirect(make_url_for('my_forms'))
    
    #pprint.pprint(queriedForm.data)
    
    if not g.current_user.canViewForm(queriedForm):
        flash(gettext("Permission needed to view form"), 'warning')
        return redirect(make_url_for('my_forms'))
    
    # We use the 'session' because forms/edit may be showing a new form without a Form() db object yet.
    populateSessionFormData(queriedForm)
    
    return render_template('inspect-form.html', form=queriedForm)


@app.route('/forms/templates', methods=['GET'])
@login_required
def list_form_templates():
    return render_template('form_templates.html', templates=formTemplates)


@app.route('/forms/new', methods=['GET'])
@app.route('/forms/new/<string:templateID>', methods=['GET'])
@enabled_user_required
def new_form(templateID=None):
    clearSessionFormData()
    if templateID:
        template = list(filter(lambda template: template['id'] == templateID, formTemplates))
        if template:
            session['formStructure']=template[0]['structure']
    
    session['afterSubmitTextMD'] = "## %s" % gettext("Thank you!!")
    return render_template('edit-form.html', host_url=g.site.host_url)


@app.route('/forms/duplicate/<string:id>', methods=['GET'])
@enabled_user_required
def duplicate_form(id):
    clearSessionFormData()
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Form is not available. 404"), 'warning')
        return redirect(make_url_for('my_forms'))
        
    populateSessionFormData(queriedForm)
    session['slug']=""
    flash(gettext("You can edit the duplicate now"), 'info')
    return render_template('edit-form.html', host_url=g.site.host_url)


@app.route('/forms/share/<string:id>', methods=['GET'])
@enabled_user_required
def share_form(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Form is not available. 404"), 'warning')
        return redirect(make_url_for('my_forms'))
    editors=queriedForm.getEditors()
    return render_template('share-form.html', form=queriedForm, editors=editors)


@app.route('/forms/add-editor/<string:id>', methods=['POST'])
@enabled_user_required
def add_editor(id):
    queriedForm = Form(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Form is not available"), 'warning')
        return redirect(make_url_for('my_forms'))
    if not 'email' in request.form:
        flash(gettext("We need an email"), 'warning')
        return redirect(make_url_for('share_form', id=queriedForm.id))
    if not isValidEmail(request.form['email']):
        return redirect(make_url_for('share_form', id=queriedForm.id))

    newEditor=User(hostname=g.site.hostname, email=request.form['email'])
    if not newEditor or newEditor.enabled==False:
        flash(gettext("Can't find a user with that email"), 'warning')
        return redirect(make_url_for('share_form', id=queriedForm.id))
    if str(newEditor._id) in queriedForm.editors:
        flash(gettext("%s is already an editor" % newEditor.email), 'warning')
        return redirect(make_url_for('share_form', id=queriedForm.id))
    
    if queriedForm.addEditor(newEditor):
        flash(gettext("New editor added ok"), 'success')
        queriedForm.addLog(gettext("Added editor %s" % newEditor.email))
    return redirect(make_url_for('share_form', id=queriedForm.id))


@app.route('/forms/remove-editor/<string:form_id>/<string:editor_id>', methods=['POST'])
@enabled_user_required
def remove_editor(form_id, editor_id):
    queriedForm = Form.find(id=form_id, editor=str(g.current_user.id))
    if not queriedForm:
        return json.dumps(False)
    if editor_id == queriedForm.author:
        return json.dumps(False)
    
    removedEditor_id=queriedForm.removeEditor(editor_id)
    try:
        editor=User.find(id=removedEditor_id).email
    except:
        editor=removedEditor_id
    queriedForm.addLog(gettext("Removed editor %s" % editor))
    return json.dumps(removedEditor_id)


@app.route('/forms/expiration/<string:id>', methods=['GET', 'POST'])
@enabled_user_required
def set_expiration_date(_id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Form is not available"), 'warning')
        return redirect(make_url_for('my_forms'))
    if request.method == 'POST':
        if 'date' in request.form and 'time' in request.form:
            if request.form['date'] and request.form['time']:
                expireDate="%s %s:00" % (request.form['date'], request.form['time'])
                if not isValidExpireDate(expireDate):
                    flash(gettext("Date-time is not valid"), 'warning')
                else:
                    queriedForm.data['expiryConditions']['expireDate']=expireDate
                    queriedForm.expired=queriedForm.hasExpired()
                    queriedForm.save()
                    queriedForm.addLog(gettext("Expiry date set to: %s" % expireDate))
            elif not request.form['date'] and not request.form['time']:
                if queriedForm.data['expiryConditions']['expireDate']:
                    queriedForm.data['expiryConditions']['expireDate']=None
                    queriedForm.expired=queriedForm.hasExpired()
                    queriedForm.save()
                    queriedForm.addLog(gettext("Expiry date cancelled"))
            else:
                flash(gettext("Missing date or time"), 'warning')
                
    return render_template('expiration.html', form=queriedForm)


@app.route('/forms/set-field-condition/<string:id>', methods=['POST'])
@enabled_user_required
def set_field_condition(_id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps({'condition': False}))

    availableFields=queriedForm.getAvailableNumberTypeFields()
    if not request.form['field_name'] in availableFields:
        return JsonResponse(json.dumps({'condition': False}))
    
    if not request.form['condition']:
        if request.form['field_name'] in queriedForm.fieldConditions:
            del queriedForm.fieldConditions[request.form['field_name']]
            queriedForm.expired=queriedForm.hasExpired()
            queriedForm.save()
        return JsonResponse(json.dumps({'condition': False}))
    
    fieldType=availableFields[request.form['field_name']]['type']
    if fieldType == "number":
        try:
            queriedForm.fieldConditions[request.form['field_name']]={
                                                            "type": fieldType,
                                                            "condition": int(request.form['condition'])
                                                        }          
            
            queriedForm.expired=queriedForm.hasExpired()
            queriedForm.save()
        except:
            return JsonResponse(json.dumps({'condition': False}))
    
    return JsonResponse(json.dumps({'condition': request.form['condition']}))


@app.route('/forms/edit', methods=['GET', 'POST'])
@app.route('/forms/edit/<string:id>', methods=['GET', 'POST'])
@enabled_user_required
def edit_form(id=None):
    #pp = pprint.PrettyPrinter(indent=4)

    ensureSessionFormKeys()
    
    session['form_id']=None
    queriedForm=None
    if id:
        print("id form-edit: %s" % id)
        queriedForm = Form.find(id=id)
        if queriedForm:
            if not queriedForm.isEditor(g.current_user):
                flash(gettext("You can't edit that form"), 'warning')
                return redirect(make_url_for('my_forms'))
            session['form_id'] = str(queriedForm.id)

    if request.method == 'POST':
        if queriedForm:
            session['slug'] = queriedForm.slug
        elif 'slug' in request.form:
            session['slug'] = sanitizeSlug(request.form['slug'])
        if not session['slug']:
            flash(gettext("Something went wrong. No slug!"), 'error')
            return redirect(make_url_for('my_forms'))

        """
        We keep a list of all the elements of the structure that have a 'name' attribute.
        These are the elements that will contain the data submitted by users and saved as form.entries in the DB
        This list of elements is called 'fieldIndex'.
        """    
        session['formFieldIndex']=[]
        
        """ formStructure is generated by formBuilder. """
        formStructure = json.loads(request.form['structure'])      
        for formElement in formStructure:
            if 'name' in formElement:
                """ formbuilder may return empty label attributes or label attributes with html. """
                if 'label' in formElement:
                    # formbuilder adds a trailing '<br>' to lables.
                    #formElement['label']=formElement['label'].rstrip('<br>')
                    if not stripHTMLTagsForLabel(formElement['label']): 
                        # we need some text (any text) to save as a label.                 
                        formElement['label'] = "Label"
                
                session['formFieldIndex'].append({'name': formElement['name'], 'label': formElement['label']})
       
        session['formStructure'] = json.dumps(formStructure)
        session['afterSubmitTextMD'] = escapeMarkdown(request.form['afterSubmitTextMD'])
        
        return redirect(make_url_for('preview_form'))

    return render_template('edit-form.html', host_url=g.site.host_url)



@app.route('/forms/check-slug-availability/<string:slug>', methods=['POST'])
@enabled_user_required
def is_slug_available(slug):
    available = True
    slug=sanitizeSlug(slug)
    if Form.find(slug=slug, hostname=g.site.hostname):
        available = False
    if slug in app.config['RESERVED_SLUGS']:
        available = False
    # we return a sanitized slug as a suggestion for the user.
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))


@app.route('/forms/preview', methods=['GET'])
@enabled_user_required
def preview_form():

    if not ('slug' in session and 'formStructure' in session):
        return redirect(make_url_for('my_forms'))
     
    # formBuilder includes tags in labels. Let's remove them
    structure=json.loads(session['formStructure'])
    for element in structure:
        if "type" in element and element["type"] != "paragraph":
            element['label']=stripHTMLTags(element['label'])
    session['formStructure']=json.dumps(structure)
    
    session['slug']=sanitizeSlug(session['slug'])
    formURL = "%s%s" % ( g.site.host_url, session['slug'])
    return render_template('preview-form.html', formURL=formURL,
                                                afterSubmitTextHTML=markdown2HTML(session['afterSubmitTextMD']))


@app.route('/forms/save', methods=['POST'])
@app.route('/forms/save/<string:id>', methods=['POST'])
@enabled_user_required
def save_form(id=None):
    
    """ We prepend the reserved field 'Created' to the index
        app.config['RESERVED_FORM_ELEMENT_NAMES'] = ['created']
    """
    session['formFieldIndex'].insert(0, {'label':gettext("Created"), 'name':'created'})
    
    afterSubmitText={   'markdown':escapeMarkdown(session['afterSubmitTextMD']),
                        'html':markdown2HTML(session['afterSubmitTextMD'])} 
    
    queriedForm = Form.find(id=id, editor=str(g.current_user.id)) if id else None    
    if queriedForm:
        # update form.fieldConditions
        savedConditionalFields = [field for field in queriedForm.fieldConditions]
        availableConditionalFields=[element["name"] 
                                    for element in json.loads(session['formStructure'])
                                    if "name" in element]
        for field in savedConditionalFields:
            if not field in availableConditionalFields:
                del queriedForm.fieldConditions[field]
        
        if queriedForm.totalEntries > 0:
            for field in queriedForm.fieldIndex:
                if not getFieldByNameInIndex(session['formFieldIndex'], field['name']):
                    """ This field was removed by the editor but there are already entries.
                        So we append it to the index. """
                    session['formFieldIndex'].append(field)
        
        queriedForm.data["structure"]=session["formStructure"]
        queriedForm.data["fieldIndex"]=session["formFieldIndex"]
        
        queriedForm.data["afterSubmitText"]=afterSubmitText
        queriedForm.save()
        
        flash(gettext("Updated form OK"), 'success')
        queriedForm.addLog(gettext("Form edited"))
        return redirect(make_url_for('inspect_form', _id=queriedForm._id))
    else:
        if not session['slug']:
            # just in case!
            flash(gettext("Slug is missing."), 'error')
            return redirect(make_url_for('edit_form'))
        if Form.find(slug=session['slug'], hostname=g.site.hostname):
            flash(gettext("Slug is not unique. %s" % session['slug']), 'error')
            return redirect(make_url_for('edit_form'))

        newFormData={
                    "created": datetime.date.today().strftime("%Y-%m-%d"),
                    "author": str(g.current_user.id),
                    "editors": {str(g.current_user.id): Form().newEditorPreferences()},
                    "postalCode": "08014",
                    "enabled": False,
                    "expired": False,
                    "expiryConditions": {"expireDate": None, "fields": {}},
                    "hostname": g.site.hostname,
                    "slug": session['slug'],
                    "structure": session['formStructure'],
                    "fieldIndex": session['formFieldIndex'],
                    "entries": [],
                    "sharedEntries": {  "enabled": False,
                                        "key": getRandomString(32),
                                        "password": None,
                                        "expireDate": None},
                    "afterSubmitText": afterSubmitText,
                    "log": [],
                    "requireDataConsent": g.site.isPersonalDataConsentEnabled(),
                    "restrictedAccess": False,
                    "adminPreferences": { "public": True }
                }
        newForm=Form.insert(newFormData)
        clearSessionFormData()
        newForm.addLog(gettext("Form created"))
        flash(gettext("Saved form OK"), 'success')
        # notify Admins
        smtpSendNewFormNotification(User().getNotifyNewFormEmails(), newForm)
        return redirect(make_url_for('inspect_form', id=newForm.id))

    clearSessionFormData()
    return redirect(make_url_for('my_forms'))
    

@app.route('/forms/delete/<string:id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_form(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Form not found"), 'warning')
        return redirect(make_url_for('my_forms'))
  
    if request.method == 'POST':
        if queriedForm.slug == request.form['slug']:
            entries = queriedForm.totalEntries
            queriedForm.delete()
            flash(gettext("Deleted '%s' and %s entries" % (queriedForm.slug, entries)), 'success')
            return redirect(make_url_for('my_forms'))
        else:
            flash(gettext("Form name does not match"), 'warning')
                   
    return render_template('delete-form.html', form=queriedForm)


@app.route('/forms/log/list/<string:id>', methods=['GET'])
@enabled_user_required
def list_log(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Form not found"), 'warning')
        return redirect(make_url_for('my_forms'))
    return render_template('list-log.html', form=queriedForm)


""" Author form settings """

@app.route('/form/toggle-enabled/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_enabled(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    enabled=queriedForm.toggleEnabled()
    queriedForm.addLog(gettext("Public set to: %s" % enabled))
    return JsonResponse(json.dumps({'enabled': enabled}))

@app.route('/form/toggle-shared-entries/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_shared_entries(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    shared=queriedForm.toggleSharedEntries()
    queriedForm.addLog(gettext("Shared entries set to: %s" % shared))
    return JsonResponse(json.dumps({'enabled':shared}))

@app.route('/form/toggle-restricted-access/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_restricted_access(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    access=queriedForm.toggleRestrictedAccess()
    queriedForm.addLog(gettext("Restricted access set to: %s" % access))
    return JsonResponse(json.dumps({'restricted':access}))

@app.route('/form/toggle-notification/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_notification(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    return JsonResponse(json.dumps({'notification':queriedForm.toggleNotification()}))

@app.route('/form/toggle-data-consent/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_dataconsent(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    dataConsentBool=queriedForm.toggleRequireDataConsent()
    queriedForm.addLog(gettext("Data protection consent set to: %s" % dataConsentBool))
    return JsonResponse(json.dumps({'consent':dataConsentBool}))

@app.route('/form/toggle-expiration-notification/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_expiration_notification(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    return JsonResponse(json.dumps({'notification':queriedForm.toggleExpirationNotification()}))


""" Form entries """

@app.route('/forms/entries/<string:id>', methods=['GET'])
@enabled_user_required
def list_entries(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("No form found"), 'warning')
        return redirect(make_url_for('my_forms'))

    return render_template('list-entries.html', form=queriedForm)


@app.route('/forms/csv/<string:id>', methods=['GET'])
@enabled_user_required
def csv_form(id):
    queriedForm = Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("No form found"), 'warning')
        return redirect(make_url_for('my_forms'))

    csv_file = writeCSV(queriedForm)
    
    @after_this_request 
    def remove_file(response): 
        os.remove(csv_file) 
        return response
    
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)

@app.route('/forms/delete-entry/<string:id>', methods=['POST'])
@enabled_user_required
def delete_entry(id):
    queriedForm=Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return json.dumps({'deleted': False})
    
    # we going to use the entry's "created" value as a unique value (gulps).
    if not "created" in request.json:
        return json.dumps({'deleted': False})
    
    foundEntries = [entry for entry in queriedForm.entries if entry['created'] == request.json["created"]]
    if not foundEntries or len(foundEntries) > 1:
        """ If there are two entries with the same 'created' value, we don't delete anything """
        return json.dumps({'deleted': False})

    queriedForm.entries.remove(foundEntries[0])    
    queriedForm.expired = queriedForm.hasExpired()
    queriedForm.save()
    queriedForm.addLog(gettext("Deleted an entry"))
    return json.dumps({'deleted': True})

@app.route('/forms/undo-delete-entry/<string:id>', methods=['POST'])
@enabled_user_required
def undo_delete_entry(id):
    queriedForm=Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        return json.dumps({'undone': False})
    
    # check we have a "created" key
    created_pos=next((i for i,field in enumerate(request.json) if "name" in field and field["name"] == "created"), None)
    if not isinstance(created_pos, int):
        return json.dumps({'undone': False})
    
    foundEntries = [entry for entry in queriedForm.entries if entry['created'] == request.json[created_pos]["value"]]
    if foundEntries:
        """ There is already an entry in the DB with the same 'created' value, we don't do anything """
        return json.dumps({'undone': False})

    entry={}
    for field in request.json:
        try:
            entry[field["name"]]=field["value"]
        except:
            return json.dumps({'undone': False})
    queriedForm.entries.append(entry)
    queriedForm.expired = queriedForm.hasExpired()
    queriedForm.save()
    queriedForm.addLog(gettext("Undeleted an entry"))
    return json.dumps({'undone': True})

@app.route('/forms/change-entry-field-value/<string:id>', methods=['POST'])
@enabled_user_required
def change_entry(id):
    queriedForm=Form.find(id=id, editor=str(g.current_user.id))
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

@app.route('/forms/delete-entries/<string:id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_entries(id):
    queriedForm=Form.find(id=id, editor=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Form not found"), 'warning')
        return redirect(make_url_for('my_forms'))

    if request.method == 'POST':
        try:
            totalEntries = int(request.form['totalEntries'])
        except:
            flash(gettext("We expected a number"), 'warning')
            return render_template('delete-entries.html', form=queriedForm)
        
        if queriedForm.totalEntries == totalEntries:
            queriedForm.deleteEntries()
            if not queriedForm.hasExpired() and queriedForm.expired:
                queriedForm.expired=False
                queriedForm.save()
            flash(gettext("Deleted %s entries" % totalEntries), 'success')
            return redirect(make_url_for('list_entries', id=queriedForm.id))
        else:
            flash(gettext("Number of entries does not match"), 'warning')
                   
    return render_template('delete-entries.html', form=queriedForm)



""" User settings """

@app.route('/user/<string:username>', methods=['GET', 'POST'])
@login_required
def user_settings(username):
    if username != g.current_user.username:
        return redirect(make_url_for('my_forms'))
    user=g.current_user
    invites=[]
    if user.isAdmin():
        invites=[Invite(id=invite['id']) for invite in Invite().findAll()]
    sites=[]
    installation=None
    if user.isRootUser():
        sites=[Site(id=site['id']) for site in Site().findAll()]
        installation=Installation()
    context = {
        'user': user,
        'invites': invites,
        'site': Site(hostname=user.hostname),
        'sites': sites,
        'installation': installation
    }
    return render_template('user-settings.html', **context)
 

@app.route('/user/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            g.current_user.setToken(email=request.form['email'])
                        
            smtpSendConfirmEmail(g.current_user, request.form['email'])
            flash(gettext("We've sent an email to %s") % request.form['email'], 'info')
            return redirect(make_url_for('user_settings', username=g.current_user.username))
            
    return render_template('change-email.html')


@app.route('/user/send-validation', methods=['GET'])
@login_required
def send_validation_email():   
    g.current_user.setToken(email=g.current_user.email)
    smtpSendConfirmEmail(g.current_user, g.current_user.email)
    flash(gettext("We've sent an email to %s") % g.current_user.email, 'info')
    return redirect(make_url_for('user_settings', username=g.current_user.username))
    

@app.route('/user/change-language', methods=['GET', 'POST'])
@login_required
def change_language():
    if request.method == 'POST':
        if 'language' in request.form and request.form['language'] in app.config['LANGUAGES']:
            g.current_user.language=request.form['language']
            g.current_user.save()
            refresh()
            flash(gettext("Language updated OK"), 'success')
            return redirect(make_url_for('user_settings', username=g.current_user.username))
            
    return render_template('change-language.html')



""" Site user management """

@app.route('/user/new', methods=['GET', 'POST'])
@app.route('/user/new/<string:token>', methods=['GET', 'POST'])
@sanitized_token
def new_user(token=None):
    if g.site.invitationOnly and not token:
        return redirect(make_url_for('index'))

    invite=None
    if token:
        invite=Invite(token=token)
        if not invite:
            flash(gettext("Invitation not found"), 'warning')
            return redirect(make_url_for('index'))
        if not isValidToken(invite.token):
            flash(gettext("Your petition has expired"), 'warning')
            invite.delete()
            return redirect(make_url_for('index'))
            
    if request.method == 'POST':
        if not isNewUserRequestValid(request.form):
            return render_template('new-user.html')
            
        validatedEmail=False
        adminSettings=User().defaultAdminSettings()
        
        if invite:
            if invite.data['email'] == request.form['email']:
                validatedEmail=True
            if invite.data['admin'] == True:
                adminSettings['isAdmin']=invite.data['admin']
                # the first admin of a new Site needs to config. SMTP before we can send emails.
                # when validatedEmail=False, a validation email fails to be sent because SMTP is not congifured.
                if not g.site.admins:
                    validatedEmail=True

        if request.form['email'] in app.config['ROOT_USERS']:
            adminSettings["isAdmin"]=True
            validatedEmail=True
            
        newUser = {
            "username": request.form['username'],
            "email": request.form['email'],
            "password": encryptPassword(request.form['password1']),
            "language": app.config['DEFAULT_LANGUAGE'],
            "hostname": g.site.hostname,
            "blocked": False,
            "admin": adminSettings,
            "validatedEmail": validatedEmail,
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "token": {}
        }
        user = User().create(newUser)
        if not user:
            flash(gettext("Opps! An error ocurred when creating the user"), 'error')
            return render_template('new-user.html')
        if invite:
            invite.delete()           
        
        thread = Thread(target=smtpSendNewUserNotification(User().getNotifyNewUserEmails(), user.username))
        thread.start()
        
        if validatedEmail == True:
            # login an invited user
            session["user_id"]=str(user._id)
            flash(gettext("Welcome!"), 'success')
            return redirect(make_url_for('my_forms'))
        else:
            user.setToken()
            smtpSendConfirmEmail(user)
            return render_template('new-user.html', site=g.site, created=True)

    session["user_id"]=None
    return render_template('new-user.html')




""" Login / Logout """

@app.route('/site/login', methods=['POST'])
@anon_required
def login():
    if 'username' in request.form and 'password' in request.form:
        user=User.find(hostname=g.site.hostname, username=request.form['username'], blocked=False)
        if user and verifyPassword(request.form['password'], user.password):
            session["user_id"]=str(user.id)
            if not user.validatedEmail:
                return redirect(make_url_for('user_settings', username=username))
            else:
                return redirect(make_url_for('my_forms'))
        session["user_id"]=None
    
    flash(gettext("Bad credentials"), 'warning')
    return redirect(make_url_for('index'))


@app.route('/site/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.pop("user_id")
    return redirect(make_url_for('index'))



""" Password recovery """

@app.route('/site/recover-password', methods=['GET', 'POST'])
@app.route('/site/recover-password/<string:token>', methods=['GET'])
@anon_required
@sanitized_token
def recover_password(token=None):
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            user = User(email=request.form['email'], blocked=False)
            if user:
                user.setToken()
                smtpSendRecoverPassword(user)
                flash(gettext("We may have sent you an email"), 'info')
            
            if not user and request.form['email'] in app.config['ROOT_USERS']:
                # root_user emails are only good for one account, across all sites.
                if not Installation.isUser(request.form['email']):
                    # auto invite root users
                    message="New root user at %s." % g.site.hostname
                    invite=Invite().create(g.site.hostname, request.form['email'], message, True)
                    return redirect(make_url_for('new_user', token=invite.token['token']))
            return redirect(make_url_for('index'))
        return render_template('recover-password.html')

    if token:
        user = User(token=token)
        if not user:
            flash(gettext("Couldn't find that token"), 'warning')
            return redirect(make_url_for('index'))
        if not isValidToken(user.token):
            flash(gettext("Your petition has expired"), 'warning')
            user.deleteToken()
            return redirect(make_url_for('index'))
        if user.blocked:
            user.deleteToken()
            flash(gettext("Your account has been blocked"), 'warning')
            return redirect(make_url_for('index'))

        user.deleteToken()
        user.data['validatedEmail']=True
        user.save()
        
        # login the user
        session['user_id']=str(user._id)
        return redirect(make_url_for('reset_password'))

    return render_template('recover-password.html')


@app.route('/site/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        if 'password1' in request.form and 'password2' in request.form:
            if not isValidPassword(request.form['password1'], request.form['password2']):
                return render_template('reset-password.html')

            g.current_user.setPassword(encryptPassword(request.form['password1']))
            g.current_user.save()
            flash(gettext("Password changed OK"), 'success')
            return redirect(make_url_for('my_forms', username=g.current_user.username))
    
    return render_template('reset-password.html')


"""
This may be used to validate a New user's email, or an existing user's Change email request
"""
@app.route('/user/validate-email/<string:token>', methods=['GET'])
@sanitized_token
def validate_email(token):
    user = User.find(token=token)
    if not user:
        flash(gettext("We couldn't find that petition"), 'warning')
        return redirect(make_url_for('index'))
    if not isValidToken(user.token):
        flash(gettext("Your petition has expired"), 'warning')
        user.deleteToken()
        return redirect(make_url_for('index'))
    
    # On a Change email request, the new email address is saved in the token.
    if 'email' in user.token:
        user.email = user.token['email']

    user.deleteToken()
    user.data['validatedEmail']=True
    user.save()
    #login the user
    session['user_id']=str(user._id)
    flash(gettext("Your email address is valid"), 'success')
    return redirect(make_url_for('user_settings', username=user.username))



""" Site settings """

@app.route('/site/save-blurb', methods=['POST'])
@admin_required
def save_blurb():
    if request.method == 'POST':
        if 'editor' in request.form:            
            g.site.saveBlurb(request.form['editor'])
            flash(gettext("Text saved OK"), 'success')
    return redirect(make_url_for('index'))


@app.route('/site/save-personal-data-consent-text', methods=['POST'])
@admin_required
def save_data_consent():
    if request.method == 'POST':
        if 'editor' in request.form:            
            g.site.savePersonalDataConsentText(request.form['editor'])
            flash(gettext("Text saved OK"), 'success')
    return redirect(make_url_for('user_settings', username=g.current_user.username))

@app.route('/site/email/config', methods=['GET', 'POST'])
@admin_required
def smtp_config():
    config=g.site.data["smtpConfig"] 
    if request.method == 'POST':
        config['host'] = request.form['host']
        config['port'] = request.form['port']
        config['encryption']=request.form['encryption'] if not request.form['encryption']=="None" else ""
        config['user'] = request.form['user']
        config['password'] = request.form['password']
        config['noreplyAddress'] = request.form['noreplyAddress']

        if not config['host']:
            flash(gettext("We need a host"), 'warning')
            return render_template('smtp-config.html', **config)
        if not config['port']:
            flash(gettext("We need a port"), 'warning')
            return render_template('smtp-config.html', **config)
        if not isValidEmail(config['noreplyAddress']):            
            flash(gettext("We need a valid sender address"), 'warning')
            return render_template('smtp-config.html', **config)

        g.site.saveSMTPconfig(**config)
        flash(gettext("Confguration saved OK"), 'success')
        return render_template('smtp-config.html', **config)
    
    return render_template('smtp-config.html', **config)

@app.route('/site/email/test-config/<string:email>', methods=['GET'])
@admin_required
def test_smtp(email):
    if isValidEmail(email):
        if smtpSendTestEmail(email):
            flash(gettext("SMTP config works!"), 'success')
    else:
        flash("Email not valid", 'warning')
    return redirect(make_url_for('smtp_config'))

@app.route('/site/change-sitename', methods=['GET', 'POST'])
@admin_required
def change_siteName():
    if request.method == 'POST':
        if 'sitename' in request.form:
            g.site.data['siteName']=request.form['sitename']
            g.site.save()
            flash(gettext("Site name changed OK"), 'success')
            return redirect(make_url_for('user_settings', username=g.current_user.username))
    return render_template('change-sitename.html', site=g.site)

@app.route('/site/change-favicon', methods=['GET', 'POST'])
@admin_required
def change_site_favicon():
    if request.method == 'POST':
        if not request.files['file']:
            flash(gettext("Required file is missing"), 'warning')
            return render_template('change-site-favicon.html')
        file=request.files['file']
        if len(file.filename) > 4 and file.filename[-4:] == ".png":
            filename="%s_favicon.png" % g.site.hostname
            file.save(os.path.join(app.config['FAVICON_FOLDER'], filename))
        else:
            flash(gettext("Bad file name. PNG only"), 'warning')
            return render_template('change-site-favicon.html')
        flash(gettext("Favicon changed OK. Refresh with  &lt;F5&gt;"), 'success')
        return redirect(make_url_for('user_settings', username=g.current_user.username))
    return render_template('change-site-favicon.html')

@app.route('/site/reset-favicon', methods=['GET'])
@admin_required
def reset_site_favicon():
    if g.site.deleteFavicon():
        flash(gettext("Favicon reset OK. Refresh with  &lt;F5&gt;"), 'success')
    return redirect(make_url_for('user_settings', username=g.current_user.username))
    
@app.route('/site/update', methods=['GET', 'POST'])
def schema_update():
    installation=Installation()
    if installation.isSchemaUpToDate():
        if g.current_user:
            flash(gettext("Schema is already up to date. Nothing to do."), 'info')
            return redirect(make_url_for('my_forms'))
        else:
            return render_template('page-not-found.html'), 400
    
    if request.method == 'POST':
        if 'secret_key' in request.form and request.form['secret_key'] == app.config['SECRET_KEY']:
            installation.updateSchema()
            flash(gettext("Updated schema OK!"), 'success')
            return redirect(make_url_for('user_settings', username=g.current_user.username))
        else:
            flash("Wrong secret", 'warning')
    
    return render_template('schema-upgrade.html', installation=installation)
    

@app.route('/admin/sites/edit/<string:hostname>', methods=['GET'])
@rootuser_required
def edit_site(hostname):
    queriedSite=Site(hostname=hostname)
    return render_template('edit-site.html', site=queriedSite)


@app.route('/admin/sites/toggle-scheme/<string:hostname>', methods=['POST'])
@rootuser_required
def toggle_site_scheme(hostname): 
    queriedSite=Site(hostname=hostname)
    return json.dumps({'scheme': queriedSite.toggleScheme()})


@app.route('/admin/sites/change-port/<string:hostname>/', methods=['POST'])
@app.route('/admin/sites/change-port/<string:hostname>/<string:port>', methods=['POST'])
@rootuser_required
def change_site_port(hostname, port=None):
    queriedSite=Site(hostname=hostname)
    if not port:
        queriedSite.data['port']=None
    else:
        try:
            int(port)
            queriedSite.data['port']=port
        except:
            pass
    queriedSite.save()
    return json.dumps({'port': queriedSite.data['port']})
    

@app.route('/admin/sites/delete/<string:hostname>', methods=['GET', 'POST'])
@rootuser_required
def delete_site(hostname):
    queriedSite=Site(hostname=hostname)
    if not queriedSite:
        flash(gettext("Site not found"), 'warning')
        return redirect(make_url_for('user_settings', username=g.current_user.username))

    if request.method == 'POST' and 'hostname' in request.form:
        if queriedSite.hostname == request.form['hostname']:
            if g.site.hostname == queriedSite.hostname:
                flash(gettext("Cannot delete current site"), 'warning')
                return redirect(make_url_for('user_settings', username=g.current_user.username)) 
            
            queriedSite.delete()
            flash(gettext("Deleted %s" % (queriedSite.host_url)), 'success')
            return redirect(make_url_for('user_settings', username=g.current_user.username))       
        else:
            flash(gettext("Site name does not match"), 'warning')
        
    return render_template('delete-site.html', site=queriedSite)




""" Admin user settings """

@app.route('/admin/toggle-newuser-notification', methods=['POST'])
@admin_required
def toggle_newUser_notification(): 
    return json.dumps({'notify': g.current_user.toggleNewUserNotification()})


@app.route('/admin/toggle-newform-notification', methods=['POST'])
@admin_required
def toggle_newForm_notification(): 
    return json.dumps({'notify': g.current_user.toggleNewFormNotification()})


@app.route('/admin/toggle-invitation-only', methods=['POST'])
@admin_required
def toggle_invitation_only(): 
    return json.dumps({'invite': g.site.toggleInvitationOnly()})

@app.route('/admin/toggle-dataprotection', methods=['POST'])
@admin_required
def toggle_site_data_consent(): 
    return json.dumps({'dataprotection_enabled': g.site.togglePersonalDataConsentEnabled()})

""" Invitations """

@app.route('/admin/invites/new', methods=['GET', 'POST'])
@admin_required
def new_invite():
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):           
            admin=False
            hostname=g.site.hostname
            if g.isRootUser:
                if 'admin' in request.form:
                    admin=True
                if 'hostname' in request.form:
                    hostname=request.form['hostname']
            if not request.form['message']:
                message="You have been invited to %s." % hostname
            else:
                message=request.form['message']
            invite=Invite().create(hostname, request.form['email'], message, admin)
            smtpSendInvite(invite)
            flash(gettext("We've sent an invitation to %s") % invite.data['email'], 'success')
            return redirect(make_url_for('user_settings', username=g.current_user.username))
    sites=[]
    if g.isRootUser:
        # rootUser can choose the site to invite to.
        sites = [site for site in Site().findAll()]

    return render_template('new-invite.html', hostname=g.site.hostname, sites=sites)


@app.route('/admin/invites/delete/<string:id>', methods=['GET'])
@admin_required
def delete_invite(_id):
    invite=Invite(_id=_id)
    if invite:
        invite.delete()
    else:
        flash(gettext("Opps! We can't find that invitation"), 'error')
    return redirect(make_url_for('user_settings', username=g.current_user.username))



""" Admin user management """

@app.route('/admin', methods=['GET'])
@app.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    return render_template('list-users.html', users=User.findAll()) 


@app.route('/admin/users/<string:id>', methods=['GET'])
@app.route('/admin/users/id/<string:id>', methods=['GET'])
@admin_required
def inspect_user(id):
    user=User.objects(id=id).first()
    if not user:
        flash(gettext("User not found"), 'warning')
        return redirect(make_url_for('list_users'))

    return render_template('inspect-user.html', user=user) 


@app.route('/admin/users/toggle-blocked/<string:id>', methods=['POST'])
@admin_required
def toggle_user_blocked(id):       
    user=User.objects(id=id).first()
    if not user:
        return JsonResponse(json.dumps())

    if user.id == g.current_user.id:
        # current_user cannot disable themself
        blocked=user.blocked
    else:
        blocked=user.toggleBlocked()
    return JsonResponse(json.dumps({'blocked':blocked}))


@app.route('/admin/users/toggle-admin/<string:id>', methods=['POST'])
@admin_required
def toggle_admin(id):       
    user=User.objects(id=id).first()
    if not user:
        return JsonResponse(json.dumps())
    
    if user.username == g.current_user.username:
        # current_user cannot remove their own admin permission
        isAdmin=True
    else:
        isAdmin=user.toggleAdmin()
    return JsonResponse(json.dumps({'admin':isAdmin}))


@app.route('/admin/users/delete/<string:id>', methods=['GET', 'POST'])
@admin_required
def delete_user(id):       
    user=User.objects(id=id).first()
    if not user:
        flash(gettext("User not found"), 'warning')
        return redirect(make_url_for('my_forms'))
  
    if request.method == 'POST' and 'username' in request.form:
        if user.isRootUser():
            flash(gettext("Cannot delete root user"), 'warning')
            return redirect(make_url_for('inspect_user', _id=user._id)) 
        if user._id == g.current_user._id:
            flash(gettext("Cannot delete yourself"), 'warning')
            return redirect(make_url_for('inspect_user', username=user.username)) 
        if user.username == request.form['username']:
            if user.delete():
                flash(gettext("Deleted user '%s'" % (user.username)), 'success')
            return redirect(make_url_for('list_users'))
        else:
            flash(gettext("Username does not match"), 'warning')
    return render_template('delete-user.html', user=user)



""" Admin form management """

@app.route('/admin/forms', methods=['GET'])
@admin_required
def list_forms():
    return render_template('list-forms.html', forms=Form.findAll()) 

@app.route('/admin/forms/toggle-public/<string:id>', methods=['GET'])
@admin_required
def toggle_form_public_admin_prefs(id):
    queriedForm = Form.objects(id=id).first()
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('my_forms'))
    queriedForm.toggleAdminFormPublic()
    return redirect(make_url_for('inspect_form', id=id))
    
@app.route('/admin/forms/change-author/<string:id>', methods=['GET', 'POST'])
@admin_required
def change_author(id):
    queriedForm = Form.objects(id=id).first()
    if not queriedForm:
        flash(gettext("Form is not available"), 'warning')
        return redirect(make_url_for('my_forms'))
    editors=queriedForm.getEditors()
    if request.method == 'POST':
        if not 'old_author_username' in request.form or not request.form['old_author_username']==queriedForm.user.username:
            flash(gettext("Current author incorrect"), 'warning')
            return render_template('change-author.html', form=queriedForm, editors=editors)
        if 'new_author_username' in request.form:
            new_author=User(username=request.form['new_author_username'], hostname=g.site.hostname)
            if new_author:
                if new_author.enabled:
                    old_author=queriedForm.user # we really need to find better property names than author and user
                    if queriedForm.changeAuthor(new_author):
                        queriedForm.addLog(gettext("Changed author from %s to %s" % (old_author.username, new_author.username)))
                        flash(gettext("Changed author OK"), 'success')
                        return redirect(make_url_for('inspect_form', id=queriedForm.id))
                else:
                    flash(gettext("Cannot use %s. The user is not enabled" % request.form['new_author_username']), 'warning')
            else:
                flash(gettext("Can't find username %s" % request.form['new_author_username']), 'warning')
    return render_template('change-author.html', form=queriedForm, editors=editors)


"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    response = Response(json_response, 'application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code=status_code
    return response
