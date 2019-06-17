from flask import request, Response, render_template, redirect, url_for, session, flash
import json, re, datetime
from formbuilder import app, mongo
from .persistence import *
from .session import *
from .utils import *

import pprint


@app.route('/', methods=['GET'])
def index():
    pp = pprint.PrettyPrinter()
    
    """
    print(mongo)    # flask_pymongo
    testDB = mongo.db 
    print(mongo.db) # Database
    print(mongo.db.list_collection_names()) # Database
    print(mongo.db.forms) #collection
    
    forms = mongo.db.forms
    
    for form in forms.find():
        pp.pprint(form)
    """
    return render_template('index.html')


@app.route('/<string:slug>', methods=['GET', 'POST'])
def view_form(slug):
    queriedForm = getForm(slug)
    if not queriedForm:
        flash("Form not found", 'error')
        return redirect(url_for('list_forms'))
    queriedForm = dict(queriedForm)
       
    if request.method == 'POST':      
        formData = dict(request.form)
        data = {}
        data["created"] = datetime.date.today().strftime("%Y/%m/%d")
        for key in formData:
            value = formData[key]
            data[key]=', '.join(value)
        
        saveEntry(queriedForm, data)
        #mongo.db.forms.update({ "_id": queriedForm["_id"] }, {"$push": {"entries": data }})
        
        #return render_template('thankyou.html', thankyouNote=queriedForm['thankyouNote'])
        return render_template('thankyou.html', thankyouNote="Thankyou !!")
        
    return render_template('view-form.html', formStructure=queriedForm['structure'])     
            

@app.route('/control', methods=['GET'])
@app.route('/control/list', methods=['GET'])
def list_forms():
    forms = sorted(findForms(), key=lambda k: k['created'], reverse=True)
    return render_template('list-forms.html', forms=forms, admin=True) 


@app.route('/list', methods=['GET'])
def list_all_forms():
    return render_template('list-forms.html', forms=findForms()) 


@app.route('/control/view-data/<string:slug>', methods=['GET'])
def form_summary(slug):
    pp = pprint.PrettyPrinter()
    queriedForm = getForm(slug)
    if not queriedForm:
        flash("No form found", 'error')
        return redirect(url_for('list_forms'))

    print(queriedForm['fieldIndex'])
    return render_template('form-data-summary.html',    slug=slug,
                                                        fieldIndex=queriedForm['fieldIndex'],
                                                        entries=queriedForm['entries'])

@app.route('/control/csv/<string:slug>', methods=['GET'])
def csv_form(slug):
    pp = pprint.PrettyPrinter()
    quieriedForm = getForm(slug)
    if not quieriedForm:
        flash("No form found", 'error')
        return redirect(url_for('list_forms'))
        
    entries=quieriedForm['entries']
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

    
    pp.pprint(fieldNames)
    
    return render_template('csv.html', fieldNames=fieldNames, entries=entries)


@app.route('/control/new', methods=['GET'])
def new_form():
    clearSessionFormData()
    return render_template('edit-form.html',    formStructure=session['formStructure'],
                                                formSlug=session['formSlug'],
                                                isFormNew=True)


@app.route('/control/edit', methods=['GET', 'POST'])
@app.route('/control/edit/<string:slug>', methods=['GET', 'POST'])
def edit_form(slug=None):
    pp = pprint.PrettyPrinter(indent=4)
    ensureSessionFormKeys() 
    if request.method == 'POST':
        if not slug:
            if 'slug' in request.form:
                session['formSlug'] = request.form['slug']
            else:
                flash("Something went wrong. No slug!", 'error')
                return redirect(url_for('list_forms'))
                
        formStructureDict = json.loads(request.form['structure'])
        fieldCount=0
        for formElement in formStructureDict:
            
            """
            We need a label for displaying Entry data (eg. csv download).
            Ensure the 'label' attribute is not empty
            """
            if 'label' in formElement and (formElement['label'] == "" or formElement['label'] == "<br>"):
                formElement['label'] = "Label for field/element"
            
            # elements with a 'name' attribute are included in 'entries' in the database
            if 'name' in formElement:
                #pp.pprint(formFieldIndex)
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

                fieldCount += 1
        
        # remove all 'user removed' fields from index
        pp.pprint(formStructureDict)
        pp.pprint(session['formFieldIndex'])
        for field in session['formFieldIndex']:
            print(field)
            if not getFieldByNameInIndex(formStructureDict, field['name']):
                session['formFieldIndex'].remove(field)

        #pp.pprint(session['formFieldIndex'])
        
        session['formStructure'] = json.dumps(formStructureDict)
        return redirect(url_for('preview_form'))

    # GET
    isFormNew = True
    if slug:
        queriedForm = getForm(slug)
        if queriedForm:
            isFormNew = False
            session['formSlug'] = queriedForm['slug']
            if not session['formStructure']:
                session['formStructure'] = queriedForm['structure']

    return render_template('edit-form.html', formStructure=session['formStructure'],
                                             slug=session['formSlug'],
                                             isFormNew=isFormNew)


@app.route('/control/preview', methods=['GET'])
def preview_form():

    if not ('formSlug' in session and 'formStructure' in session):
        return redirect(url_for('list_forms'))
    
    #pp = pprint.PrettyPrinter()
    #pp.pprint(session['formStructure'])
    
    formURL = "%s%s" % ( request.url_root, session['formSlug'])
    return render_template('preview-form.html', formStructure=session['formStructure'], \
                                                formURL=formURL, \
                                                slug=session['formSlug'])


@app.route('/control/save/<string:slug>', methods=['POST'])
def save_form(slug):
        if slug != session['formSlug']:
            flash("Something went wrong", 'error')
        
        slug = sanitizeSlug(slug)
        session['formFieldIndex'].insert(0, {'label':'created', 'name':'created'})
        if getForm(slug):
            # slug should be unique so Let's update this form
            updateForm(slug, { 
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
                        "urlRoot": request.url_root,
                        "slug": slug,
                        "structure": session['formStructure'],
                        "fieldIndex": session['formFieldIndex'],
                        "entries": [],
                        "afterSubmitNote": "Thankyou!!"
                    }
            insertForm(newFormData)
            clearSessionFormData()
            flash("Saved OK", 'info')

        return redirect(url_for('admin_form', slug=slug))


@app.route('/control/admin/<string:slug>', methods=['GET'])
def admin_form(slug):
    queriedForm = getForm(slug)
    if queriedForm:
        populateSessionFormData(queriedForm)
    else:
        clearSessionFormData()
        flash("Form not found", 'warning')
        return redirect(url_for('list_forms'))
       
    formURL = "%s%s" % ( request.url_root, session['formSlug'])
    return render_template('admin-form.html',   formStructure=session['formStructure'], \
                                                slug=slug, \
                                                created=queriedForm['created'],
                                                total_entries=getTotalEntries(queriedForm),
                                                last_entry_date=getLastEntryData(queriedForm),
                                                formURL=formURL)
        
    

@app.route('/control/check-slug-availability/<string:slug>', methods=['POST'])
def is_slug_available(slug): 
    slug = sanitizeSlug(slug)
    available = True
    if getForm(slug):
        available = False
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))


"""
Used to respond to Ajax requests
"""
def JsonResponse(json_response="1", status_code=200):
    response = Response(json_response, 'application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code=status_code
    return response
