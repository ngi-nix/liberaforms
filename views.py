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
from urllib.parse import urlparse
from flask_babel import gettext, refresh
from .persitence import *
from .session import *
from .utils import *
from .email import *
from form_templates import formTemplates

import pprint


@app.before_request
def before_request():
    g.current_user=None
    g.isRootUser=False
    g.isAdmin=False
    if 'username' in session:
        g.current_user=User(username=session['username'])
        if g.current_user and g.current_user.isRootUser():
            g.isRootUser=True
        if g.current_user and g.current_user.admin:
            g.isAdmin=True

@babel.localeselector
def get_locale():
    if g.current_user:
        return g.current_user.language
    else:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


@app.route('/', methods=['GET'])
def index():
    
    """
    forms= mongo.db.forms.find()
    for form in forms:
        form["notification"]={"newEntry": True}
        mongo.db.forms.save(form)    
    """
    """
    for site in Site().findAll():    #mongo objects
        site['scheme']=urlparse(request.host_url).scheme
        mongo.db.sites.save(site)
    """
    
    return render_template('index.html',site=Site(), isAdmin=g.isAdmin)


@app.route('/<string:slug>', methods=['GET', 'POST'])
@sanitized_slug_required
def view_form(slug):
    queriedForm = Form(slug=slug)
    if not (queriedForm and queriedForm.isPublic()):
        flash(gettext("Form is not available. 404"), 'warning')
        if g.current_user:
            return redirect(url_for('my_forms'))
        return redirect(url_for('index'))
       
    if request.method == 'POST':  
        formData=request.form.to_dict(flat=False)
        entry = {}
        entry["created"] = datetime.date.today().strftime("%Y-%m-%d")
        
        for key in formData:
            value = formData[key]
            if isinstance(value, list): # A checkboxes-group contains multiple values 
                value=', '.join(value) # convert list of values to a string
                key=key.rstrip('[]') # remove tailing '[]' from the name attrib (appended by formbuilder)
            entry[key]=value
            
        #print("save entry: %s" % formData)
        queriedForm.saveEntry(entry)
        
        if queriedForm.notification['newEntry'] == True:
            user=User(username=queriedForm.author)
            data=[]
            for field in queriedForm.fieldIndex:
                if field['name'] in entry:
                    data.append( (stripHTMLTags(field['label']), entry[field['name']]) )
            smtpSendNewFormEntryNotification(user.email, data, queriedForm.slug)
        
        return render_template('thankyou.html', form=queriedForm)
        
    return render_template('view-form.html', formStructure=queriedForm.structure)     
            

@app.route('/forms', methods=['GET'])
@login_required
def my_forms():
    forms = sorted(Form().findAll(author=g.current_user.username), key=lambda k: k['created'], reverse=True)
    return render_template('my-forms.html', forms=forms, username=g.current_user.username) 


@app.route('/forms/view-data/<string:slug>', methods=['GET'])
@login_required
@sanitized_slug_required
def list_entries(slug):
    queriedForm = Form(slug=slug, author=g.current_user.username)
    if not queriedForm:
        flash(gettext("No form found"), 'warning')
        return redirect(url_for('my_forms'))

    return render_template('list-entries.html', form=queriedForm,
                                                fieldIndex=removeHTMLFromLabels(queriedForm.fieldIndex))


@app.route('/forms/csv/<string:slug>', methods=['GET'])
@login_required
@sanitized_slug_required
def csv_form(slug):
    queriedForm = Form(slug=slug, author=g.current_user.username)
    if not queriedForm:
        flash(gettext("No form found"), 'warning')
        return redirect(url_for('my_forms'))

    csv_file = writeCSV(queriedForm)
    
    @after_this_request 
    def remove_file(response): 
        os.remove(csv_file) 
        return response
    
    return send_file(csv_file, mimetype="text/csv", as_attachment=True)


@app.route('/forms/templates', methods=['GET'])
@login_required
def list_form_templates():

    return render_template('form_templates.html', templates=formTemplates)


@app.route('/forms/new', methods=['GET'])
@app.route('/forms/new/<string:templateID>', methods=['GET'])
@login_required
def new_form(templateID=None):
    clearSessionFormData()
    if templateID:
        template = list(filter(lambda template: template['id'] == templateID, formTemplates))
        if template:
            session['formStructure']=template[0]['structure']
    
    session['afterSubmitTextMD'] = "## %s" % gettext("Thank you!!")
    return render_template('edit-form.html', isFormNew=True)


@app.route('/forms/edit', methods=['GET', 'POST'])
@app.route('/forms/edit/<string:slug>', methods=['GET', 'POST'])
@login_required
def edit_form(slug=None):
    #pp = pprint.PrettyPrinter(indent=4)
    
    ensureSessionFormKeys()
    if request.method == 'POST':
        
        if not (slug or 'slug' in request.form):
            flash(gettext("Something went wrong. No slug!"), 'error')
            return redirect(url_for('my_forms'))
        if slug and slug != session['slug']:
            flash(gettext("Something went wrong. Bad slug!"), 'error')
            return redirect(url_for('my_forms'))
        if 'slug' in request.form:
            session['slug'] = sanitizeSlug(request.form['slug'])
        
        """
        We keep a list of all the elements of the structure that have a 'name' attribute.
        These are the elements that will contain the data submitted by users as form.entries in the DB
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
                    formElement['label']=formElement['label'].rstrip('<br>')
                    if not stripHTMLTags(formElement['label']): 
                        # we need some text (any text) to save as a label.                 
                        formElement['label'] = "Label"
                
                session['formFieldIndex'].append({'name': formElement['name'], 'label': formElement['label']})
       
        session['formStructure'] = json.dumps(formStructure)
        session['afterSubmitTextMD'] = escapeMarkdown(request.form['afterSubmitTextMD'])
        
        return redirect(url_for('preview_form'))

    # GET
    isFormNew = True
    if slug:
        queriedForm = Form(slug=sanitizeSlug(slug))
        if queriedForm:
            isFormNew = False
            if queriedForm.author != g.current_user.username:
                flash(gettext("You can't edit that form"), 'warning')
                return redirect(url_for('my_forms'))
            
    return render_template('edit-form.html', isFormNew=isFormNew, user=g.current_user)



@app.route('/forms/preview', methods=['GET'])
@login_required
def preview_form():

    if not ('slug' in session and 'formStructure' in session):
        return redirect(url_for('my_forms'))
    
    formURL = "%s%s" % ( Site().host_url, session['slug'])
    return render_template('preview-form.html', formURL=formURL,
                                                afterSubmitTextHTML=markdown2HTML(session['afterSubmitTextMD']),
                                                slug=sanitizeSlug(session['slug']))



@app.route('/forms/save/<string:slug>', methods=['POST'])
@login_required
@sanitized_slug_required
def save_form(slug):
    if slug != session['slug']:
        flash(gettext("Something went wrong. Bad slug!"), 'error')
    
    """ We prepend the field 'Created' to the index """
    session['formFieldIndex'].insert(0, {'label':'Created', 'name':'created'})
    
    afterSubmitText={   'markdown':escapeMarkdown(session['afterSubmitTextMD']),
                        'html':markdown2HTML(session['afterSubmitTextMD'])} 

    queriedForm=Form(slug=session['slug'])
    if queriedForm:
        if queriedForm.author != g.current_user.username:
            flash(gettext("You can't edit that form"), 'warning')
            return redirect(url_for('my_forms'))
     
        if queriedForm.totalEntries > 0:
            for field in queriedForm.fieldIndex:
                if not getFieldByNameInIndex(session['formFieldIndex'], field['name']):
                    """ This field was removed by the author but there are entries.
                        So we append it to the index. """
                    session['formFieldIndex'].append(field)
        
        queriedForm.update({    "structure": session['formStructure'], 
                                "fieldIndex": session['formFieldIndex'],
                                "afterSubmitText": afterSubmitText })
        flash(gettext("Updated form OK"), 'success')
    else:
        newFormData={
                    "created": datetime.date.today().strftime("%Y-%m-%d"),
                    "author": session['username'],
                    "postalCode": "08014",
                    "enabled": False,
                    "hostname": urlparse(request.host_url).hostname,
                    "slug": slug,
                    "notification": {"newEntry": True},
                    "structure": session['formStructure'],
                    "fieldIndex": session['formFieldIndex'],
                    "entries": [],
                    "afterSubmitText": afterSubmitText
                }
        if Form().insert(newFormData):
            flash(gettext("Saved form OK"), 'success')
            # notify Admins
            smtpSendNewFormNotification(User().getNotifyNewFormEmails(), slug)

    clearSessionFormData()
    return redirect(url_for('inspect_form', slug=slug))


@app.route('/forms/delete/<string:slug>', methods=['GET', 'POST'])
@login_required
@sanitized_slug_required
def delete_form(slug):
    queriedForm=Form(slug=slug, author=g.current_user.username)
    if not queriedForm:
        flash(gettext("Form not found"), 'warning')
        return redirect(url_for('my_forms'))
  
    if request.method == 'POST':
        if queriedForm.slug == request.form['slug']:
            entries = queriedForm.totalEntries
            queriedForm.delete()
            flash(gettext("Deleted '%s' and %s entries" % (slug, entries)), 'success')
            return redirect(url_for('my_forms'))
        else:
            flash(gettext("Form name does not match"), 'warning')
                   
    return render_template('delete-form.html', form=queriedForm)


@app.route('/forms/delete-entries/<string:slug>', methods=['GET', 'POST'])
@login_required
@sanitized_slug_required
def delete_entries(slug):
    queriedForm=Form(slug=slug, author=g.current_user.username)
    if not queriedForm:
        flash(gettext("Form not found"), 'warning')
        return redirect(url_for('my_forms'))

    if request.method == 'POST':
        try:
            totalEntries = int(request.form['totalEntries'])
        except:
            flash(gettext("We expected a number"), 'warning')
            return render_template('delete-entries.html', form=queriedForm)
        
        if queriedForm.totalEntries == totalEntries:
            queriedForm.deleteEntries()
            flash(gettext("Deleted %s entries" % queriedForm.totalEntries), 'success')
            return redirect(url_for('list_entries', slug=queriedForm.slug))
        else:
            flash(gettext("Number of entries does not match"), 'warning')
                   
    return render_template('delete-entries.html', form=queriedForm)


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
@sanitized_slug_required
def inspect_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        #clearSessionFormData()
        flash(gettext("No form found"), 'warning')
        return redirect(url_for('my_forms'))        
    
    if not g.current_user.canViewForm(queriedForm):
        flash(gettext("Sorry, no permission to view that form"), 'warning')
        return redirect(url_for('my_forms'))
    
    # We use the 'session' because forms/edit maybe showing a new form without a Form() db object yet.
    populateSessionFormData(queriedForm)

    user=User(username=queriedForm.author)
    # there should be a user with this username in the database. But just in case..
    userEnabled=None
    if user:
        userEnabled=user.enabled
    
    return render_template('inspect-form.html', form=queriedForm, userEnabled=userEnabled)
        


@app.route('/user/<string:username>', methods=['GET', 'POST'])
@login_required
def user_settings(username):
    user=User(username=username)
    if not user:
        return redirect(url_for('my_forms'))
    if not (user.username == g.current_user.username or g.current_user.admin):
        return redirect(url_for('my_forms'))
    thisSite=Site()
    invites=[]
    if user.admin:
        invites=Invite().findAll()
        if thisSite.data['scheme'] != urlparse(request.host_url).scheme:
            # background maintenance.
            # maybe a letsencrypt cert got insalled after the initial installation and http is now https.
            thisSite.data['scheme'] = urlparse(request.host_url).scheme
            thisSite.save()
    
    sites=[]
    if g.isRootUser:
        for site in Site().findAll():    #mongo objects
            site=Site(hostname=site['hostname'])
            totalForms = Form().findAll(hostname=site.hostname).count()
            totalUsers = User().findAll(hostname=site.hostname).count()
            sites.append({'site':site, 'totalUsers': totalUsers, 'totalForms':totalForms})
            
    return render_template('user-settings.html', user=user, invites=invites, site=thisSite, sites=sites)
 


@app.route('/user/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        if 'email' in request.form and isValidEmail(request.form['email']):
            g.current_user.setToken(email=request.form['email'])
                        
            smtpSendConfirmEmail(g.current_user, request.form['email'])
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
            refresh()
            flash(gettext("Language updated OK"), 'success')
            return redirect(url_for('user_settings', username=g.current_user.username))
            
    return render_template('change-language.html')


@app.route('/user/new', methods=['GET', 'POST'])
@app.route('/user/new/<string:token>', methods=['GET', 'POST'])
@sanitized_token
def new_user(token=None):
    if Site().invitationOnly and not token:
        return redirect(url_for('index'))

    invite=None
    if token:
        invite=Invite(token=token)
        if not invite:
            flash(gettext("Invitation not found"), 'warning')
            return redirect(url_for('index'))
        if not isValidToken(invite.token):
            invite.delete()
            flash(gettext("This invitation has expired"), 'warning')
            return redirect(url_for('index'))
            
    if request.method == 'POST':
        if not isNewUserRequestValid(request.form):
            return render_template('new-user.html')
            
        isEnabled=False
        adminSettings=User().defaultAdminSettings
        
        if invite and invite.data['admin'] == True:
            adminSettings['isAdmin']=invite.data['admin']
        
        if request.form['email'] in app.config['ROOT_USERS']:
            adminSettings["isAdmin"]=True
            isEnabled=True
        
        newUser = {
            "username": request.form['username'],
            "email": request.form['email'],
            "password": encryptPassword(request.form['password1']),
            "language": app.config['DEFAULT_LANGUAGE'],
            "hostname": Site().hostname,
            "enabled": isEnabled,
            "admin": adminSettings,
            "validatedEmail": False,
            "created": datetime.date.today().strftime("%Y-%m-%d"),
            "token": {}
        }
        user = User().create(newUser)
        if not user:
            flash(gettext("Opps! An error ocurred when creating the user"), 'error')
            return render_template('new-user.html')

        if invite:
            invite.delete()

        user.setToken()
        smtpSendConfirmEmail(user)
        
        if user.isRootUser():
            #login a new root user
            session['username']=user.username
            return redirect(url_for('user_settings', username=user.username))
        else:
            # notify Admins
            smtpSendNewUserNotification(User().getNotifyNewUserEmails(), user.username)
            
        return render_template('new-user.html', site=Site(), created=True)

    session['username']=None
    g.current_user=None
    return render_template('new-user.html')


@app.route('/admin/users/delete/<string:username>', methods=['GET', 'POST'])
@rootuser_required
def delete_user(username):
    user=User(username=username)
    if not user:
        flash(gettext("User not found"), 'warning')
        return redirect(url_for('my_forms'))
  
    if request.method == 'POST' and 'username' in request.form:
        if user.email in app.config['ROOT_USERS']:
            flash(gettext("Cannot delete root user"), 'warning')
            return redirect(url_for('inspect_user', username=user.username))  
        if user.username == g.current_user.username:
            flash(gettext("Cannot delete yourself"), 'warning')
            return redirect(url_for('inspect_user', username=user.username)) 
        if user.username == request.form['username']:
            user.delete()
            flash(gettext("Deleted user '%s'" % (user.username)), 'success')
            return redirect(url_for('list_users'))
        else:
            flash(gettext("Username does not match"), 'warning')
                   
    return render_template('delete-user.html', username=user.username)


@app.route('/admin/sites/delete/<string:hostname>', methods=['GET', 'POST'])
@rootuser_required
def delete_site(hostname):
    queriedSite=Site(hostname=hostname)
    if not queriedSite:
        flash(gettext("Site not found"), 'warning')
        return redirect(url_for('user_settings', username=g.current_user.username))

    if request.method == 'POST' and 'hostname' in request.form:
        if queriedSite.hostname == request.form['hostname']:
            if Site().hostname == queriedSite.hostname:
                flash(gettext("Cannot delete current site"), 'warning')
                return redirect(url_for('user_settings', username=g.current_user.username)) 
            
            queriedSite.delete()
            flash(gettext("Deleted %s" % (queriedSite.host_url)), 'success')
            return redirect(url_for('user_settings', username=g.current_user.username))       
        else:
            flash(gettext("Site name does not match"), 'warning')
        
    return render_template('delete-site.html', site=queriedSite)



@app.route('/site/login', methods=['POST'])
@anon_required
def login():
    if 'username' in request.form and 'password' in request.form:
        user=User(username=request.form['username'])
        if user and user.enabled and verifyPassword(request.form['password'], user.data['password']):
            session['username']=user.username
            return redirect(url_for('my_forms'))
    
    flash(gettext("Bad credentials"), 'warning')
    return redirect(url_for('index'))


@app.route('/site/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session['username']=None
    return redirect(url_for('index'))


@app.route('/site/recover-password', methods=['GET', 'POST'])
@app.route('/site/recover-password/<string:token>', methods=['GET'])
@anon_required
@sanitized_token
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
                invite=Invite().create(Site().hostname, request.form['email'], message, True)
                return redirect(url_for('new_user', token=invite.token['token']))
            
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
        #g.current_user=user
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
@sanitized_token
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
    #g.current_user=user
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
            admin=False
            hostname=Site().hostname
            
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
            print(invite.invite)
            smtpSendInvite(invite)
            
            flash(gettext("We sent an invitation to %s") % invite.data['email'], 'success')
            return redirect(url_for('user_settings', username=g.current_user.username))
            
    sites=[]
    if g.isRootUser:
        # rootUser can choose the site to invite to.
        for site in Site().findAll():   # iterate the cursor
            sites.append(site)

    return render_template('new-invite.html', hostname=Site().hostname, sites=sites)


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
    form=Form(slug=sanitizeSlug(slug), author=g.current_user.username)
    if not form:
        return JsonResponse(json.dumps())
        
    return JsonResponse(json.dumps({'enabled':form.toggleEnabled()}))


@app.route('/forms/toggle-notification/<string:slug>', methods=['POST'])
@login_required
def toggle_form_notification(slug):
    form=Form(slug=sanitizeSlug(slug), author=g.current_user.username)
    if not form:
        return JsonResponse(json.dumps())

    return JsonResponse(json.dumps({'notification':form.toggleNotification()}))


"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    response = Response(json_response, 'application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code=status_code
    return response
