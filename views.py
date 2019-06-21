from flask import request, Response, render_template, redirect, url_for, session, flash
import json, re, datetime
from formbuilder import app, mongo
from .forms import *
from .session import *
from .utils import *
from .users import *
from .email import *

import pprint


@app.route('/', methods=['GET'])
def index():
    pp = pprint.PrettyPrinter()
    
    
    return render_template('index.html')


@app.route('/<string:slug>', methods=['GET', 'POST'])
def view_form(slug):
    queriedForm = Form(slug=slug)
    if not queriedForm:
        flash("Form not found", 'error')
        return redirect(url_for('index'))
       
    if request.method == 'POST':      
        formData = dict(request.form)
        data = {}
        data["created"] = datetime.date.today().strftime("%Y/%m/%d")
        
        for key in formData:
            value = formData[key]
            data[key]=', '.join(value)
        
        queriedForm.saveEntry(data)
        
        #return render_template('thankyou.html', thankyouNote=queriedForm['thankyouNote'])
        return render_template('thankyou.html', thankyouNote="Thankyou !!")
        
    return render_template('view-form.html', formStructure=queriedForm.structure)     
            

@app.route('/forms', methods=['GET'])
@app.route('/forms/list', methods=['GET'])
def my_forms():
    forms = sorted(Form().findAll(author="tuttle"), key=lambda k: k['created'], reverse=True)
    return render_template('my-forms.html', forms=forms) 


@app.route('/forms/view-data/<string:slug>', methods=['GET'])
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
    
    
        #pp.pprint(entry)
        #for field in entry:
        #    print(field)

    
    #pp.pprint(fieldNames)
    
    return render_template('csv.html', fieldNames=fieldNames, entries=entries)


@app.route('/forms/new', methods=['GET'])
def new_form():
    clearSessionFormData()
    return render_template('edit-form.html',    formStructure=session['formStructure'],
                                                formSlug=session['formSlug'],
                                                isFormNew=True)


@app.route('/forms/edit', methods=['GET', 'POST'])
@app.route('/forms/edit/<string:slug>', methods=['GET', 'POST'])
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
                print('field name: %s' % field['name'])
                
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
            # slug should be unique so Let's update this form
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
                        "author": "tuttle",
                        "postalCode": "08014",
                        "enabled": False,
                        "urlRoot": request.url_root,
                        "slug": slug,
                        "structure": session['formStructure'],
                        "fieldIndex": session['formFieldIndex'],
                        "entries": [],
                        "afterSubmitNote": "Thankyou!!"
                    }
            Form().insert(newFormData)
            clearSessionFormData()
            flash("Saved OK", 'info')

        return redirect(url_for('author_form', slug=slug))


@app.route('/forms/check-slug-availability/<string:slug>', methods=['POST'])
def is_slug_available(slug): 
    slug = sanitizeSlug(slug)
    available = True
    if Form(slug=slug):
        available = False
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))


@app.route('/forms/<string:slug>', methods=['GET'])
def author_form(slug):
    queriedForm = Form(slug=slug)
    if queriedForm:
        populateSessionFormData(queriedForm.data)
    else:
        clearSessionFormData()
        flash("Form not found", 'warning')
        return redirect(url_for('my_forms'))
       
    formURL = "%s%s" % ( request.url_root, session['formSlug'])
    return render_template('author-form.html',   formStructure=session['formStructure'], \
                                                form=queriedForm.data,
                                                slug=slug, \
                                                created=queriedForm.data['created'],
                                                total_entries=getTotalEntries(queriedForm.data),
                                                last_entry_date=getLastEntryDate(queriedForm.data),
                                                formURL=formURL)
        

@app.route('/user/<string:username>', methods=['GET', 'POST'])
def user_settings(username): 
    return render_template('user-settings.html', username=username)


@app.route('/user/new', methods=['GET', 'POST'])
def new_user(): 
    if request.method == 'POST':
        if not isNewUserRequestValid(request.form):
            return render_template('new-user.html')
        newUser = {
            "username": request.form['username'],
            "email": request.form['email'],
            "password": hashPassword(request.form['password1']),
            "enabled": False,
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
    flash("Your email is valid.", 'info')
    return redirect(url_for('my_forms'))
    

@app.route('/admin', methods=['GET'])
@app.route('/admin/users', methods=['GET'])
def list_users():
    return render_template('list-users.html', users=User().findAll()) 


@app.route('/admin/user/<string:username>', methods=['GET'])
def admin_user(username):
    user = User(username=username)
    if not user:
        flash("username not in database", 'info')
        return redirect(url_for('list_users'))

    return render_template('admin-user.html',   user=user.data,
                                                formCount=user.authoredFormsCount(),
                                                forms=Form().findAll(author=username)
                                                ) 


@app.route('/admin/user/toggle-enabled/<string:username>', methods=['POST'])
def toggle_user(username): 
    user=User(username=username)
    if not user:
        return JsonResponse(json.dumps())

    return JsonResponse(json.dumps({'enabled':user.toggleEnabled()}))


@app.route('/admin/forms', methods=['GET'])
def list_all_forms():
    return render_template('list-forms.html', forms=findForms()) 


@app.route('/admin/form/toggle-enabled/<string:slug>', methods=['POST'])
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
