from formbuilder import app
from flask import session
import json

def ensureSessionFormKeys():
    if not 'formSlug' in session:
        session['formSlug'] = ""
    if not 'formFieldIndex' in session:
        session['formFieldIndex'] = []
    if not 'formStructure' in session:
        session['formStructure'] = json.dumps([])

def populateSessionFormData(queriedForm):
    session['formSlug'] = queriedForm['slug']
    session['formFieldIndex'] = queriedForm['fieldIndex']
    session['formStructure'] = queriedForm['structure']

def clearSessionFormData():
    session['formSlug'] = ""
    session['formFieldIndex'] = []
    session['formStructure'] = json.dumps([])
