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
    
    print(mongo)    # flask_pymongo
    testDB = mongo.db 
    print(mongo.db) # Database
    print(mongo.db.list_collection_names()) # Database
    print(mongo.db.forms) #collection
    
    forms = mongo.db.forms
    
    for form in forms.find():
        pp.pprint(form)

    return render_template('index.html')


@app.route('/<string:slug>', methods=['GET', 'POST'])
def view_form(slug):
    queriedForm = mongo.db.forms.find_one({"slug": slug})
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
        
        mongo.db.forms.update({ "_id": queriedForm["_id"] }, {"$push": {"entries": data }})
        
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
    fieldNames = list(fieldNames)
    # Move reserved 'created' field to fieldNames[0]
    fieldNames.insert(0, fieldNames.pop(fieldNames.index("created")))
    print(fieldNames)
    
    pp.pprint(fieldNames)
    
    return render_template('form-data-summary.html',    slug=slug,
                                                        fieldNames=fieldNames,
                                                        entries=entries)

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
    session['formSlug'] = ""
    session['formStructure'] = json.dumps([])
    
    return render_template('edit-form.html',    formStructure=session['formStructure'],
                                                formSlug=session['formSlug'],
                                                formIsNew="true")


@app.route('/control/edit', methods=['GET', 'POST'])
@app.route('/control/edit/<string:slug>', methods=['GET', 'POST'])
def edit_form(slug=None):            
    if request.method == 'POST':
        formStructureDict = json.loads(request.form['structure'])
        
        pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(formStructureDict)
        
        """
        Ensure all fields have a label. We need labels for mongo documents.
        """
        uniqueLabels = []
        uniqueNames = []

        labelCnt = 0
        for formField in formStructureDict:
            if 'label' in formField:
                if formField['label'] in app.config['RESERVED_FORM_ELEMENT_NAMES'] or formField['label'] in uniqueLabels or formField['label'] == "" or formField['label'] == "<br>":
                    while "Field name %s" % labelCnt in uniqueLabels:
                        labelCnt += 1
                    formField['label'] = "Field name %s" % labelCnt
                uniqueLabels.append(formField['label'])
                
                #create fieldName based on fieldLabel
                name = formField['label'].replace(" ", "-")
                name = name.replace("<br>", "") # formBuilder appends "<br>" to the label.
                name = name.replace("\"", "") # remove problematic chars
                name = name.replace("'", "") 
                if name in uniqueNames:
                    cnt=0
                    while "%s-%s" % (name, cnt) in uniqueNames:
                        cnt += 1
                    name = "%s-%s" % (name, cnt)
                    uniqueNames.append(name)
                formField['name'] = name
                
        #pp.pprint(formStructureDict)
        session['formStructure'] = json.dumps(formStructureDict)
        session['formSlug'] = request.form['slug']
        
        return redirect(url_for('preview_form'))

    # GET
    ensureSessionFormKeys()
    formIsNew = True
    if slug:
        queriedForm = getForm(slug)
        if queriedForm and not session['formStructure']:
            session['formSlug'] = queriedForm['slug']
            session['formStructure'] = queriedForm['structure']
            formIsNew = False
        #else:
        #    session['formSlug'] = slug

    return render_template('edit-form.html', formStructure=session['formStructure'],
                                             slug=session['formSlug'],
                                             formIsNew=formIsNew)



@app.route('/control/preview', methods=['GET'])
def preview_form():

    if not ('formSlug' in session and 'formStructure' in session):
        return redirect(url_for('list_forms'))
      
    formURL = "%s%s" % ( request.url_root, session['formSlug'])
    return render_template('preview-form.html', formStructure=session['formStructure'], \
                                                formURL=formURL, \
                                                slug=session['formSlug'])


@app.route('/control/save/<string:slug>', methods=['POST'])
def save_form(slug):
        if slug != session['formSlug']:
            flash("Something went wrong", 'error')
        
        slug = sanitizeSlug(slug)        
        if getForm(slug):
            # slug should be unique so Let's update this form
            updateForm(slug, {"structure": session['formStructure']})
            flash("Updated OK", 'info')
        else:
            newFormData={
                        "created": datetime.date.today().strftime("%Y/%m/%d"),
                        "author": "tuttle",
                        "urlRoot": request.url_root,
                        "slug": slug,
                        "structure": session['formStructure'],
                        "entries": [],
                        "afterSubmitNote": "Thankyou!!"
                    }
            insertForm(newFormData)
            emptySessionFormData()
            flash("Saved OK", 'info')
        return redirect(url_for('admin_form', slug=slug))


@app.route('/control/admin/<string:slug>', methods=['GET'])
def admin_form(slug):
    queriedForm = getForm(slug)
    if queriedForm:
        session['formSlug'] = queriedForm['slug']
        session['formStructure'] = queriedForm['structure']
    else:
        session['formSlug'] = ""
        session['formStructure'] = json.dumps([])
        flash("Form not found", 'warning')
        return redirect(url_for('list_forms'))
    
    total_entries = len(queriedForm["entries"])
    if total_entries:
        last_entry = queriedForm["entries"][-1] 
        last_entry_date = last_entry["created"]
    else:
        last_entry_date = ""
    
    formURL = "%s%s" % ( request.url_root, session['formSlug'])
    return render_template('admin-form.html',   formStructure=session['formStructure'], \
                                                slug=session['formSlug'], \
                                                created=queriedForm['created'],
                                                total_entries=total_entries,
                                                last_entry_date=last_entry_date,
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
