"""
“Copyright 2019 La Coordinadora d’Entitats la Lleialtat Santsenca”

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

from flask import request, g, Response, render_template, redirect, url_for, session, flash, send_file
import json, re, datetime
from formbuilder import app, mongo
from functools import wraps
from urllib.parse import urlparse
from .persitence import *
from .session import *
from .utils import *
from .email import *

import pprint


@app.before_request
def before_request():
    g.current_user=None
    if 'username' in session:
        g.current_user=User(username=session['username'])
    g.hostname = urlparse(request.host_url).hostname


# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user and g.current_user.admin:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


def anon_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user:
            return redirect(url_for('index'))
        else:
            return f(*args, **kwargs)
    return wrap


@app.route('/', methods=['GET'])
def index():
    #pp = pprint.PrettyPrinter()
    
    """
    users= mongo.db.users.find()
    for user in users:
        user["language"] = app.config['DEFAULT_LANGUAGE']
        mongo.db.users.save(user)
    """
    isAdmin=False
    if g.current_user and g.current_user.admin:
        isAdmin=True
    return render_template('index.html',    blurb = Site().blurb,
                                            isAdmin=isAdmin)


@app.route('/<string:slug>', methods=['GET', 'POST'])
def view_form(slug):
    queriedForm = Form(slug=slug)
    if not (queriedForm and queriedForm.isAvailable()):
        flash("Form is not available. 404", 'warning')
        if g.current_user:
            return redirect(url_for('my_forms'))
        return redirect(url_for('index'))
       
    if request.method == 'POST':      
        formData = dict(request.form)
        data = {}
        data["created"] = datetime.date.today().strftime("%Y-%m-%d")
        
        for key in formData:
            value = formData[key]
            data[key]=', '.join(value)      #value is possibly a list
        
        queriedForm.saveEntry(data)
        
        #return render_template('thankyou.html', thankyouNote=queriedForm['thankyouNote'])
        return render_template('thankyou.html', thankyouNote="Thankyou !!")
        
    return render_template('view-form.html', formStructure=queriedForm.structure)     
            

@app.route('/forms', methods=['GET'])
@login_required
def my_forms():
    forms = sorted(Form().findAll(author=g.current_user.username), key=lambda k: k['created'], reverse=True)
    return render_template('my-forms.html', forms=forms, username=g.current_user.username) 


@app.route('/forms/view-data/<string:slug>', methods=['GET'])
@login_required
def form_summary(slug):
    #pp = pprint.PrettyPrinter()
    queriedForm = Form(slug=slug)
    if not queriedForm:
        flash("No form found", 'error')
        return redirect(url_for('my_forms'))
        
    if not queriedForm.isAuthor(g.current_user):
        flash("You are not the form author and cannot view this data", 'warning')
        return redirect(url_for('my_forms'))

    #print(queriedForm['fieldIndex'])
    return render_template('form-data-summary.html',    slug=slug,
                                                        fieldIndex=queriedForm.fieldIndex,
                                                        entries=queriedForm.entries)


@app.route('/forms/csv/<string:slug>', methods=['GET'])
@login_required
def csv_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        flash("No form found", 'error')
        return redirect(url_for('my_forms'))
        
    if not queriedForm.isAuthor(g.current_user):
        flash("No permissions", 'warning')
        return redirect(url_for('my_forms'))
    
    csv_file = writeCSV(queriedForm)
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)



@app.route('/forms/new', methods=['GET'])
@login_required
def new_form():
    clearSessionFormData()
    return render_template('edit-form.html',    formStructure=session['formStructure'],
                                                formSlug=session['formSlug'],
                                                isFormNew=True)



@app.route('/forms/edit', methods=['GET', 'POST'])
@app.route('/forms/edit/<string:slug>', methods=['GET', 'POST'])
@login_required
def edit_form(slug=None):
    #pp = pprint.PrettyPrinter(indent=4)
    ensureSessionFormKeys()
    if request.method == 'POST':
        if not slug:
            if 'slug' in request.form:
                session['formSlug'] = request.form['slug']
            else:
                flash("Something went wrong. No slug!", 'error')
                return redirect(url_for('my_forms'))
        
        queriedForm=Form(slug=session['formSlug'])
        queriedFieldIndex=[]
        if queriedForm:
            if not g.current_user.canEditForm(queriedForm):
                return redirect(url_for('my_forms'))
            queriedFieldIndex=queriedForm.fieldIndex   
        
        formStructureDict = json.loads(request.form['structure'])
        fieldCount=0
        for formElement in formStructureDict:
            
            # elements with a 'name' attribute are included in 'entries' in the database
            if 'name' in formElement:
                # We need a label for displaying 'entry' data (eg. csv download).
                if 'label' in formElement and (formElement['label'] == "" or formElement['label'] == "<br>"):
                    formElement['label'] = "Label for field/element"

                # Have we already included this field in the index?
                field = getFieldByNameInIndex(session['formFieldIndex'], formElement['name'])
                if field:
                    """
                    We want to order the fields for when we displaying Entry data (eg. csv download).
                    """    
                    fieldPosition = session['formFieldIndex'].index(field)
                    if field['label'] != formElement['label'] or fieldPosition != fieldCount:                      
                        # user changed 'label' attribute or the position of the field.
                        updatedField={'name': formElement['name'], 'label': formElement['label']}
                        session['formFieldIndex'].remove(field)
                        session['formFieldIndex'].insert(fieldCount, updatedField)
                else:
                    newField={'name': formElement['name'], 'label': formElement['label']}
                    session['formFieldIndex'].insert(fieldCount, newField)

                if field in queriedFieldIndex:
                    queriedFieldIndex.remove(field)
                fieldCount += 1
        
        # pp.pprint(queriedFieldIndex)
        
        # these fields are no longer present in formStructureDict. (removed by user).
        orphanedFieldNames = [d['name'] for d in queriedFieldIndex if 'name' in d]
        # if there are no 'entries', we will delete them from session['formFieldIndex']
        entries=[]
        if queriedForm:
            entries=queriedForm.entries
            #pp.pprint(entries)
        
        if not entries:
            # remove all 'user removed' fields from index
            for field in session['formFieldIndex']:
                #print('field name: %s' % field['name'])
                
                if not getFieldByNameInIndex(formStructureDict, field['name']):
                    # need to check if an 'entry' has already been saved with this field.
                    if field['name'] in orphanedFieldNames:
                        if field['name'] in app.config['RESERVED_FORM_ELEMENT_NAMES']:
                            # don't remove special field we have incluede (eg 'created')
                            continue
                        session['formFieldIndex'].remove(field)
        
        session['formStructure'] = json.dumps(formStructureDict)
        return redirect(url_for('preview_form'))

    # GET
    isFormNew = True
    if slug:
        queriedForm = Form(slug=slug)
        if queriedForm:
            isFormNew = False
            if not g.current_user.canEditForm(queriedForm):
                return redirect(url_for('my_forms'))
            session['formSlug'] = queriedForm.slug
            if not session['formStructure']:
                session['formStructure'] = queriedForm.structure

    return render_template('edit-form.html', formStructure=session['formStructure'],
                                             slug=session['formSlug'],
                                             isFormNew=isFormNew,
                                             user=g.current_user)



@app.route('/forms/preview', methods=['GET'])
@login_required
def preview_form():

    if not ('formSlug' in session and 'formStructure' in session):
        return redirect(url_for('my_forms'))
    
    #pp = pprint.PrettyPrinter()
    #pp.pprint(session['formStructure'])
    
    formURL = "%s%s" % ( request.url_root, session['formSlug'])
    return render_template('preview-form.html', formStructure=session['formStructure'], \
                                                formURL=formURL, \
                                                slug=session['formSlug'])



@app.route('/forms/save/<string:slug>', methods=['POST'])
@login_required
def save_form(slug):
        if slug != session['formSlug']:
            flash("Something went wrong", 'error')
        
        if not getFieldByNameInIndex(session['formFieldIndex'], 'created'):
            session['formFieldIndex'].insert(0, {'label':'Created', 'name':'created'})
        else:
            # move 'created' field to beginning of the Index
            field = getFieldByNameInIndex(session['formFieldIndex'], 'created')
            session['formFieldIndex'].remove(field)
            session['formFieldIndex'].insert(0, field)
        
        slug = sanitizeSlug(slug)
        queriedForm=Form(slug=slug)
        if queriedForm:
            if not g.current_user.canEditForm(queriedForm):
                return redirect(url_for('my_forms'))
            
            queriedForm.update({ 
                                "structure": session['formStructure'],
                                "fieldIndex": session['formFieldIndex']
                                })

            #pp = pprint.PrettyPrinter(indent=4)
            #pp.pprint(newFormData)
            
            flash("Updated form OK", 'success')
        else:
            newFormData={
                        "created": datetime.date.today().strftime("%Y-%m-%d"),
                        "author": session['username'],
                        "postalCode": "08014",
                        "enabled": False,
                        "hostname": urlparse(request.host_url).hostname,
                        "slug": slug,
                        "notification": [],
                        "structure": session['formStructure'],
                        "fieldIndex": session['formFieldIndex'],
                        "entries": [],
                        "afterSubmitNote": "Thankyou!!"
                    }
            Form().insert(newFormData)
            clearSessionFormData()
            flash("Saved form OK", 'success')

        return redirect(url_for('inspect_form', slug=slug))



@app.route('/forms/check-slug-availability/<string:slug>', methods=['POST'])
@login_required
def is_slug_available(slug): 
    slug = sanitizeSlug(slug)
    available = True
    if Form(slug=slug):
        available = False
    # we return a sanitized slug as a suggestion for the user.
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))



@app.route('/forms/view/<string:slug>', methods=['GET'])
@login_required
def inspect_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        #clearSessionFormData()
        flash("Form not found", 'warning')
        return redirect(url_for('my_forms'))        
    
    if not g.current_user.canViewForm(queriedForm):
        return redirect(url_for('my_forms'))
    
    populateSessionFormData(queriedForm.data)

    user=User(username=queriedForm.author)
    # there should be a user with this username in the database. But just in case..
    userEnabled=None
    if user:
        userEnabled=user.enabled
    
    formURL = "%s%s" % ( request.url_root, session['formSlug'])
    return render_template('inspect-form.html', formStructure=session['formStructure'],
                                                form=queriedForm.data,
                                                slug=slug,
                                                created=queriedForm.created,
                                                total_entries=queriedForm.totalEntries,
                                                last_entry_date=queriedForm.lastEntryDate,
                                                userEnabled=userEnabled,
                                                formURL=formURL)
        


@app.route('/user/<string:username>', methods=['GET', 'POST'])
@login_required
def user_settings(username):
    user=User(username=username)
    if not user:
        return redirect(url_for('my_forms'))
    if not (user.username == g.current_user.username or g.current_user.admin):
        return redirect(url_for('my_forms'))
        
    return render_template('user-settings.html', user=user)
 


@app.route('/user/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            g.current_user.setToken(email=request.form['email'])
                        
            smtpSendConfirmEmail(g.current_user)
            flash("We sent an email to %s" % request.form['email'], 'info')
            return redirect(url_for('user_settings', username=g.current_user.username))
            
    return render_template('change-email.html')



@app.route('/user/new', methods=['GET', 'POST'])
def new_user(): 
    if request.method == 'POST':
        if not isNewUserRequestValid(request.form):
            return render_template('new-user.html')
        isAdmin=False
        isEnabled=False
        if request.form['email'] in app.config['ROOT_ADMINS']:
            isAdmin=True
            isEnabled=True
        newUser = {
            "username": request.form['username'],
            "email": request.form['email'],
            "password": encryptPassword(request.form['password1']),
            "language": app.config['DEFAULT_LANGUAGE'],
            "hostname": urlparse(request.host_url).hostname,
            "enabled": isEnabled,
            "admin": isAdmin,
            "validatedEmail": False,
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "token": {}
        }
        user = createUser(newUser)
        if not user:
            flash("An error creating the new user", 'error')
            return render_template('new-user.html')
            
        user.setToken()
        smtpSendConfirmEmail(user)
        return render_template('new-user.html', created=True)

    session['username']=None
    g.current_user=None
    return render_template('new-user.html')



@app.route('/site/login', methods=['POST'])
def login():
    if 'username' in request.form and 'password' in request.form:
        user=User(username=request.form['username'])

        if user and user.enabled and verifyPassword(request.form['password'], user.data['password']):
            if user.isRootUser() or user.hostname == g.hostname:
                session['username']=user.username
                g.current_user=user
                return redirect(url_for('my_forms'))
    
    flash("Bad credentials", 'error')
    return redirect(url_for('index'))



@app.route('/site/recover-password', methods=['GET', 'POST'])
@app.route('/site/recover-password/<string:token>', methods=['GET'])
@anon_required
def recover_password(token=None):
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            user = User(email=request.form['email'])
            if user:
                user.setToken()
                print('/site/recover-password/%s' % user.token['token'])

            flash("We may have sent you an email", 'info')
            return redirect(url_for('index'))
        return render_template('recover-password.html')

    if token:
        user = User(token=token)
        if not user:
            return redirect(url_for('index'))
        if user.hasTokenExpired():
            return redirect(url_for('index'))
        if not user.enabled:
            return redirect(url_for('index'))
            
        session['username']=user.username
        g.current_user=user

        user.deleteToken()
        return redirect(url_for('reset_password'))

    return render_template('recover-password.html')


@app.route('/site/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        if 'password1' in request.form and 'password2' in request.form:
            if not isValidPassword(request.form['password1'], request.form['password2']):
                return render_template('reset-password.html')
        
            user=g.current_user
            if user:
                user.setPassword(encryptPassword(request.form['password1']))
                user.save()
                flash("Password changed OK", 'success')
                return redirect(url_for('user_settings', username=user.username))
    
    return render_template('reset-password.html')
        

@app.route('/site/save-blurb', methods=['POST'])
@admin_required
def save_blurb():
    if request.method == 'POST':
        print(request.form)
        if 'editor' in request.form:
            
            site=Site().saveBlurb(request.form['editor'])
            flash("Text saved OK", 'success')
    return redirect(url_for('index'))
            
            

@app.route('/site/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session['username']=None
    return redirect(url_for('index'))



@app.route('/user/validate-email/<string:token>', methods=['GET'])
def validate_email(token):
    user = User(token=token)
    if not user:
        return redirect(url_for('index'))
    if user.hasTokenExpired():
        user.deleteToken()
        flash("Your petition has expired. Try again.", 'info')
        return redirect(url_for('user_settings', username=user.username))
    
    if 'email' in user.token:
        user.email = user.token['email']
    
    user.setValidatedEmail(True)
    user.setEnabled(True)
    user.deleteToken()
    session['username']=user.username
    g.current_user=user
    flash("Your email is valid.", 'success')
    return redirect(url_for('user_settings', username=user.username))
    


@app.route('/admin', methods=['GET'])
@app.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    users = User().findAll()
    userFormCount={}
    for user in users:
        userFormCount[user['username']]=User(username=user['username']).totalForms()
    return render_template('list-users.html', users=User().findAll(), userFormCount=userFormCount) 



@app.route('/admin/users/<string:username>', methods=['GET'])
@admin_required
def inspect_user(username):
    user=User(username=username)
    if not user:
        flash("Username not found", 'warning')
        return redirect(url_for('list_users'))

    return render_template('inspect-user.html', user=user.data,
                                                formCount=user.totalForms,
                                                forms=Form().findAll(author=username)
                                                ) 


@app.route('/admin/users/toggle-enabled/<string:username>', methods=['POST'])
@admin_required
def toggle_user(username): 
    user=User(username=username)
    if not user:
        return JsonResponse(json.dumps())

    if user.username == g.current_user.username:
        # current_user cannot remove login permission
        enabled=user.enabled
    else:
        enabled=user.toggleEnabled()
    return JsonResponse(json.dumps({'enabled':enabled}))


@app.route('/admin/users/toggle-admin/<string:username>', methods=['POST'])
@admin_required
def toggle_admin(username): 
    user=User(username=username)
    if not user:
        return JsonResponse(json.dumps())
    
    if user.username == g.current_user.username:
        # current_user cannot remove their own admin permission
        isAdmin=True
    else:
        isAdmin=user.toggleAdmin()
    return JsonResponse(json.dumps({'admin':isAdmin}))


@app.route('/admin/forms', methods=['GET'])
@admin_required
def list_all_forms():
    #print(Form().findAll())
    return render_template('list-forms.html', forms=Form().findAll()) 


@app.route('/forms/toggle-enabled/<string:slug>', methods=['POST'])
@login_required
def toggle_form(slug):
    form=Form(slug=slug)
    if not form:
        return JsonResponse(json.dumps())
    if not g.current_user.username == form.author:
        # don't toggle
        return JsonResponse(json.dumps({'enabled':form.enabled}))
        
    return JsonResponse(json.dumps({'enabled':form.toggleEnabled()}))


"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    response = Response(json_response, 'application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code=status_code
    return response
