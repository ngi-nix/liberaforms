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

import json, re, datetime, os
from flask import request, g, Response, render_template, redirect, url_for, session, flash, send_file, after_this_request
from GNGforms import app, mongo, babel
from functools import wraps
from urllib.parse import urlparse
from flask_babel import gettext
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


@babel.localeselector
def get_locale():
    if g.current_user:
        return g.current_user.language
    else:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

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

def rootuser_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user and g.current_user.isRootUser():
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
    
    """
    users= mongo.db.users.find()
    for user in users:
        user["admin"]=User().defaultAdminSettings
        user["language"] = app.config['DEFAULT_LANGUAGE']
        mongo.db.users.save(user)
    """
    
    isAdmin=False
    if g.current_user and g.current_user.admin:
        isAdmin=True
    return render_template('index.html',site=Site(), isAdmin=isAdmin)


@app.route('/<string:slug>', methods=['GET', 'POST'])
def view_form(slug):
    queriedForm = Form(slug=slug)
    if not (queriedForm and queriedForm.isPublished()):
        flash(gettext("Form is not available. 404"), 'warning')
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
        
        #return render_template('thankyou.html', slug=slug, thankyouNote=queriedForm['thankyouNote'])
        return render_template('thankyou.html', slug=slug, thankyouNote="Thankyou !!")
        
    return render_template('view-form.html', formStructure=queriedForm.structure)     
            

@app.route('/forms', methods=['GET'])
@login_required
def my_forms():
    forms = sorted(Form().findAll(author=g.current_user.username), key=lambda k: k['created'], reverse=True)
    return render_template('my-forms.html', forms=forms, username=g.current_user.username) 


@app.route('/forms/view-data/<string:slug>', methods=['GET'])
@login_required
def form_summary(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        flash(gettext("No form found"), 'warning')
        return redirect(url_for('my_forms'))
        
    if not queriedForm.isAuthor(g.current_user):
        flash(gettext("Permission required. You cannot view this data"), 'warning')
        return redirect(url_for('my_forms'))

    return render_template('form-data-summary.html',    slug=slug,
                                                        fieldIndex=queriedForm.fieldIndex,
                                                        entries=queriedForm.entries)


@app.route('/forms/csv/<string:slug>', methods=['GET'])
@login_required
def csv_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        flash(gettext("No form found"), 'warning')
        return redirect(url_for('my_forms'))
        
    if not queriedForm.isAuthor(g.current_user):
        flash(gettext("Permission required. You cannot view this data"), 'warning')
        return redirect(url_for('my_forms'))

    csv_file = writeCSV(queriedForm)
    
    @after_this_request 
    def remove_file(response): 
        os.remove(csv_file) 
        return response
    
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)


from .form_templates import formTemplates
@app.route('/forms/templates', methods=['GET'])
@login_required
def list_form_templates():
   
      
    return render_template('form-templates.html', templates=formTemplates)



@app.route('/forms/new', methods=['GET'])
@app.route('/forms/new/<string:templateID>', methods=['GET'])
@login_required
def new_form(templateID=None):
    clearSessionFormData()
    if templateID:
        template = list(filter(lambda template: template['id'] == templateID, formTemplates))
        if template:
            session['formStructure']=template[0]['structure']
    
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
                flash(gettext("Something went wrong. No slug!"), 'error')
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
            flash(gettext("Something went wrong. No slug!"), 'error')
        
        if not getFieldByNameInIndex(session['formFieldIndex'], 'created'):
            session['formFieldIndex'].insert(0, {'label':'Created', 'name':'created'})
        else:
            # move 'created' field to beginning of the Index
            field = getFieldByNameInIndex(session['formFieldIndex'], 'created')
            session['formFieldIndex'].remove(field)
            session['formFieldIndex'].insert(0, field)
        
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
            
            flash(gettext("Updated form OK"), 'success')
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
            if Form().insert(newFormData):
                clearSessionFormData()
                flash(gettext("Saved form OK"), 'success')

        return redirect(url_for('inspect_form', slug=slug))


@app.route('/forms/delete/<string:slug>', methods=['POST'])
@login_required
def delete_form(slug):
    queriedForm=Form(slug=slug)
    if queriedForm:
        if g.current_user.username == queriedForm.author:
            entries = queriedForm.totalEntries
            queriedForm.delete()
            flash(gettext("Deleted '%s' and %s entries" % (slug, entries)), 'success')

    return redirect(url_for('my_forms'))


@app.route('/forms/check-slug-availability/<string:slug>', methods=['POST'])
@login_required
def is_slug_available(slug):
    available = True
    slug=sanitizeSlug(slug)
    if Form(slug=slug):
        available = False
    if slug in app.config['RESERVED_SLUGS']:
        available = False
    # we return a sanitized slug as a suggestion for the user.
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))


@app.route('/forms/view/<string:slug>', methods=['GET'])
@login_required
def inspect_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        #clearSessionFormData()
        flash(gettext("No form found"), 'warning')
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
    site=None
    invites=None
    if user.admin:
        site=Site()
        invites=Invite().findAll()
        
    return render_template('user-settings.html', user=user, invites=invites, site=site)
 


@app.route('/user/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            g.current_user.setToken(email=request.form['email'])
                        
            smtpSendConfirmEmail(g.current_user)
            flash(gettext("We sent an email to %s") % request.form['email'], 'info')
            return redirect(url_for('user_settings', username=g.current_user.username))
            
    return render_template('change-email.html')


@app.route('/user/change-language', methods=['GET', 'POST'])
@login_required
def change_language():
    if request.method == 'POST':
        if 'language' in request.form and request.form['language'] in app.config['LANGUAGES']:
            g.current_user.language=request.form['language']
            g.current_user.save()
            
            flash(gettext("Language updated OK"), 'success')
            return redirect(url_for('user_settings', username=g.current_user.username))
            
    return render_template('change-language.html')


@app.route('/user/new', methods=['GET', 'POST'])
@app.route('/user/new/<string:inviteToken>', methods=['GET', 'POST'])
def new_user(inviteToken=None):
    if Site().invitationOnly and not inviteToken:
        return redirect(url_for('index'))
    if inviteToken:
        invite=Invite(token=inviteToken)
        if not invite:
            flash(gettext("Invitation not found"), 'warning')
            return redirect(url_for('index'))
        if not isValidToken(invite.token):
            deleteToken()
            flash(gettext("This invitation has expired"), 'warning')
            return redirect(url_for('index'))
            
    if request.method == 'POST':
        if not isNewUserRequestValid(request.form):
            return render_template('new-user.html')
            
        admin=User().defaultAdminSettings
        isEnabled=False
        
        if request.form['email'] in app.config['ROOT_USERS']:
            admin["isAdmin"]=True
            isEnabled=True
        newUser = {
            "username": request.form['username'],
            "email": request.form['email'],
            "password": encryptPassword(request.form['password1']),
            "language": app.config['DEFAULT_LANGUAGE'],
            "hostname": urlparse(request.host_url).hostname,
            "enabled": isEnabled,
            "admin": admin,
            "validatedEmail": False,
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "token": {}
        }
        user = createUser(newUser)
        if not user:
            flash(gettext("Opps! An error ocurred when creating the user"), 'error')
            return render_template('new-user.html')
        
        user.setToken()
        smtpSendConfirmEmail(user)
        
        if inviteToken:
            Invite(token=inviteToken).delete()
        if user.isRootUser():
            #login a new root user
            session['username']=user.username
            return redirect(url_for('user_settings', username=user.username))
            
        return render_template('new-user.html', site=Site(), created=True)

    session['username']=None
    g.current_user=None
    return render_template('new-user.html')



@app.route('/site/login', methods=['POST'])
def login():
    if 'username' in request.form and 'password' in request.form:
        user=User(username=request.form['username'])
        if user and user.enabled and verifyPassword(request.form['password'], user.data['password']):
            #if user.isRootUser() or user.hostname == Site().hostname:
            session['username']=user.username
            g.current_user=user
            return redirect(url_for('my_forms'))
    
    flash(gettext("Bad credentials"), 'error')
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
                smtpSendRecoverPassword(user)
                flash(gettext("We may have sent you an email"), 'info')
                
            if not user and request.form['email'] in app.config['ROOT_USERS']:
                message="New root user at %s." % Site().hostname
                invite=Invite().create(request.form['email'], message)
                return redirect(url_for('new_user', inviteToken=invite.token['token']))
            
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

        # login the user
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
                flash(gettext("Password changed OK"), 'success')
                return redirect(url_for('user_settings', username=user.username))
    
    return render_template('reset-password.html')
        

@app.route('/site/save-blurb', methods=['POST'])
@admin_required
def save_blurb():
    if request.method == 'POST':
        if 'editor' in request.form:            
            Site().saveBlurb(request.form['editor'])
            flash(gettext("Text saved OK"), 'success')
    return redirect(url_for('index'))
            

@app.route('/site/email/change-noreply', methods=['GET', 'POST'])
@admin_required
def change_noreply_email():
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            Site().noreplyEmailAddress=request.form['email']
            
            flash(gettext("Site email address updated OK"), 'success')
            return redirect(url_for('user_settings', username=g.current_user.username))
            
    return render_template('change-email.html')


@app.route('/site/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session['username']=None
    return redirect(url_for('index'))



@app.route('/site/test-smtp/<string:email>', methods=['GET'])
@rootuser_required
def test_smtp(email):
    if isValidEmail(email):
        if smtpSendTestEmail(email):
            flash(gettext("SMTP config works!"), 'success')
    else:
        flash("Email not valid", 'warning')
    return redirect(url_for('user_settings', username=g.current_user.username))



"""
This may be used to validate a New user's email, or an existing user's Change email request
"""
@app.route('/user/validate-email/<string:token>', methods=['GET'])
def validate_email(token):
    user = User(token=token)
    if not user:
        return redirect(url_for('index'))
    if not isValidToken(user.token):
        user.deleteToken()
        flash(gettext("Your petition has expired. Try again."), 'info')
        return redirect(url_for('index'))
    
    # On a Change email request, the new email address is saved in the token.
    if 'email' in user.token:
        user.email = user.token['email']
    
    user.setValidatedEmail(True)
    user.setEnabled(True)
    user.deleteToken()
    session['username']=user.username
    g.current_user=user
    flash(gettext("Your email address is valid"), 'success')
    return redirect(url_for('user_settings', username=user.username))
    


@app.route('/admin', methods=['GET'])
@app.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    users = User().findAll()
    userFormCount={}
    # use lambda here to avoid two findAll() calls?
    for user in users:
        userFormCount[user['username']]=User(username=user['username']).totalForms()
    return render_template('list-users.html', users=User().findAll(), userFormCount=userFormCount) 


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
    return json.dumps({'invite': Site().toggleInvitationOnly()})


@app.route('/admin/invites/new', methods=['GET', 'POST'])
@admin_required
def new_invite():
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            if not request.form['message']:
                message="You have been invited to %s." % Site().hostname
            else:
                message=request.form['message']

            invite=Invite().create(request.form['email'], message)
            smtpSendInvite(invite)
            
            flash(gettext("We sent an invitation to %s") % invite.data['email'], 'success')
            return redirect(url_for('user_settings', username=g.current_user.username))

    return render_template('new-invite.html')


@app.route('/admin/invites/delete/<string:email>', methods=['GET'])
@admin_required
def delete_invite(email):
    if not isValidEmail(email):
        flash(gettext("Opps! We got a bad email"), 'error')
    else:
        invite=Invite(email=email)
        if invite:
            invite.delete()
        else:
            flash(gettext("Opps! We can't find that invitation"), 'error')
        
    return redirect(url_for('user_settings', username=g.current_user.username))
    


@app.route('/admin/users/<string:username>', methods=['GET'])
@admin_required
def inspect_user(username):
    user=User(username=username)
    if not user:
        flash(gettext("Username not found"), 'warning')
        return redirect(url_for('list_users'))

    return render_template('inspect-user.html', user=user,
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
        # current_user cannot remove their own login permission
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
