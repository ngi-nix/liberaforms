from flask import request, g, Response, render_template, redirect, url_for, session, flash
import json, re, datetime
from formbuilder import app, mongo
from functools import wraps
from .persitence import *
from .session import *
from .utils import *
from .email import *

import pprint



@app.before_request
def before_request():
    g.current_user=None
    if 'username' in session:
        user=User(username=session['username'])
        g.current_user = user


# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        #print kwargs
        print("session[username] %s" % session['username'])
        if 'username' in session and session['username']:
            print('user is logged in.')
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.current_user and g.current_user.admin:
        #if 'admin' in session and session['admin']:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


def anon_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username' in session and session['username']:
            return redirect(url_for('index'))
        else:
            return f(*args, **kwargs)
    return wrap


@app.route('/', methods=['GET'])
def index():
    pp = pprint.PrettyPrinter()
    
    
    return render_template('index.html')


@app.route('/<string:slug>', methods=['GET', 'POST'])
def view_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        return redirect(url_for('index'))
    if not queriedForm.enabled:
        return redirect(url_for('index'))
    if not User(username=queriedForm.author).enabled:
        return redirect(url_for('index'))
       
    if request.method == 'POST':      
        formData = dict(request.form)
        data = {}
        data["created"] = datetime.date.today().strftime("%Y/%m/%d")
        
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
    forms = sorted(Form().findAll(author=session['username']), key=lambda k: k['created'], reverse=True)
    return render_template('my-forms.html', forms=forms, username=session['username']) 


@app.route('/forms/view-data/<string:slug>', methods=['GET'])
@login_required
def form_summary(slug):
    #pp = pprint.PrettyPrinter()
    queriedForm = Form(slug=slug)
    if not queriedForm:
        flash("No form found", 'error')
        return redirect(url_for('my_forms'))

    #print(queriedForm['fieldIndex'])
    return render_template('form-data-summary.html',    slug=slug,
                                                        fieldIndex=queriedForm.fieldIndex,
                                                        entries=queriedForm.entries)


@app.route('/forms/csv/<string:slug>', methods=['GET'])
@login_required
def csv_form(slug):
    pp = pprint.PrettyPrinter()
    quieriedForm = Form(slug=slug)
    if not quieriedForm:
        flash("No form found", 'error')
        return redirect(url_for('my_forms'))
        
    entries=quieriedForm.entries
    """
    We could get field names form quieriedForm but the form
    Author may have modified fields during the campaign. So,
    We build a list of fields taken from the entries.
    """
    
    fieldNames = []
    for entry in entries:
        fieldNames = set(fieldNames).union(set(list(entry.keys())))
    
    
    
    return render_template('csv.html', fieldNames=fieldNames, entries=entries)



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
                    We want to order the fields for displaying Entry data (eg. csv download).
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
            session['formSlug'] = queriedForm.slug
            if not session['formStructure']:
                session['formStructure'] = queriedForm.structure

    return render_template('edit-form.html', formStructure=session['formStructure'],
                                             slug=session['formSlug'],
                                             isFormNew=isFormNew)



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
        
        slug = sanitizeSlug(slug)
        if not getFieldByNameInIndex(session['formFieldIndex'], 'created'):
            session['formFieldIndex'].insert(0, {'label':'Created', 'name':'created'})
        else:
            # move 'created' field to beginning of the list
            field = getFieldByNameInIndex(session['formFieldIndex'], 'created')
            session['formFieldIndex'].remove(field)
            session['formFieldIndex'].insert(0, field)
        
        queriedForm=Form(slug=slug)
        if queriedForm:
            queriedForm.update({ 
                                "structure": session['formStructure'],
                                "fieldIndex": session['formFieldIndex']
                                })

            #pp = pprint.PrettyPrinter(indent=4)
            #pp.pprint(newFormData)
            
            flash("Updated OK", 'info')
        else:
            newFormData={
                        "created": datetime.date.today().strftime("%Y/%m/%d"),
                        "author": session['username'],
                        "postalCode": "08014",
                        "enabled": False,
                        "urlRoot": request.url_root,
                        "slug": slug,
                        "notification": [],
                        "structure": session['formStructure'],
                        "fieldIndex": session['formFieldIndex'],
                        "entries": [],
                        "afterSubmitNote": "Thankyou!!"
                    }
            Form().insert(newFormData)
            clearSessionFormData()
            flash("Saved OK", 'info')

        return redirect(url_for('inspect_form', slug=slug))



@app.route('/forms/check-slug-availability/<string:slug>', methods=['POST'])
@login_required
def is_slug_available(slug): 
    slug = sanitizeSlug(slug)
    available = True
    if Form(slug=slug):
        available = False
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))



@app.route('/forms/view/<string:slug>', methods=['GET'])
@login_required
def inspect_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        #clearSessionFormData()
        flash("Form not found", 'warning')
        return redirect(url_for('my_forms'))        
    
    
    populateSessionFormData(queriedForm.data)

    user=User(username=queriedForm.author)
    userEnabled=None
    # there should be a user with this username in the database. But just in case..
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
    return render_template('user-settings.html', username=username)



@app.route('/user/new', methods=['GET', 'POST'])
def new_user(): 
    if request.method == 'POST':
        if not isNewUserRequestValid(request.form):
            return render_template('new-user.html')
        isAdmin=False
        isEnabled=False
        if request.form['email'] in app.config['DEFAULT_ADMINS']:
            isAdmin=True
            isEnabled=True
        newUser = {
            "username": request.form['username'],
            "email": request.form['email'],
            "password": encryptPassword(request.form['password1']),
            "enabled": isEnabled,
            "admin": isAdmin,
            "validatedEmail": False,
            "created": datetime.date.today().strftime("%Y/%m/%d"),
            "token": {}
        }
        user = createUser(newUser)
        if not user:
            flash("An error", 'info')
            return render_template('new-user.html')
            
        user.setToken()
        sendNewUserEmail(user.data)
        return render_template('new-user.html', created=True)

    return render_template('new-user.html')



@app.route('/site/login', methods=['POST'])
def login():
    if 'username' in request.form and 'password' in request.form:
        user=User(username=request.form['username'])

        if user and user.enabled and verifyPassword(request.form['password'], user.data['password']):
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
                print('/site/recover-password/%s' % user.token)

            flash("We may have sent you an email", 'info')
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
        
            user=User(username=session['username'])
            if user:
                user.setPassword(encryptPassword(request.form['password1']))
                user.save()
                g.current_user=user
                return redirect(url_for('my_forms'))
    
    return render_template('reset-password.html')
        

@app.route('/site/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session['username']=None
    session['admin'] = False
    return redirect(url_for('index'))



@app.route('/user/validate-email/<string:token>', methods=['GET'])
def validate_email(token):
    user = User(token=token)
    if not user:
        return redirect(url_for('index'))
    if user.hasTokenExpired():
        user.deleteToken()
        flash("Your petition has expired", 'info')
        return redirect(url_for('index'))
    
    user.setValidatedEmail(True)
    user.setEnabled(True)
    user.deleteToken()
    session['username']=user.username
    g.current_user=user
    flash("Your email is valid.", 'info')
    return redirect(url_for('my_forms'))
    


@app.route('/admin', methods=['GET'])
@app.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    users = User().findAll()
        #return render_template('list-forms.html', forms=Form().findAll()) 

    userFormCount={}
    for user in users:
        userFormCount[user['username']]=User(username=user['username']).totalForms()
    return render_template('list-users.html', users=User().findAll(), userFormCount=userFormCount) 
    #print(users)
    return render_template('list-users.html', users=users)



@app.route('/admin/users/<string:username>', methods=['GET'])
@admin_required
def inspect_user(username):
    user = User(username=username)
    if not user:
        flash("username not in database", 'info')
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

    return JsonResponse(json.dumps({'enabled':user.toggleEnabled()}))


@app.route('/admin/users/toggle-admin/<string:username>', methods=['POST'])
@admin_required
def toggle_admin(username): 
    user=User(username=username)
    if not user:
        return JsonResponse(json.dumps())
    
    # current_user cannot remove their own admin permission
    if user.username == g.current_user.username:
        isAdmin=True
    else:
        isAdmin=user.toggleAdmin()
    return JsonResponse(json.dumps({'admin':isAdmin}))


@app.route('/admin/forms', methods=['GET'])
@admin_required
def list_all_forms():
    #print(Form().findAll())
    return render_template('list-forms.html', forms=Form().findAll()) 


@app.route('/admin/forms/toggle-enabled/<string:slug>', methods=['POST'])
@admin_required
def toggle_form(slug): 
    form=Form(slug=slug)
    if not form:
        return JsonResponse(json.dumps())

    return JsonResponse(json.dumps({'enabled':form.toggleEnabled()}))



"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    response = Response(json_response, 'application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code=status_code
    return response
