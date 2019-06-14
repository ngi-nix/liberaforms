from formbuilder import app
from flask import session
import json

def ensureSessionFormKeys():
    if not 'formSlug' in session:
        session['formSlug'] = ""
    if not 'formStructure' in session:
        session['formStructure'] = json.dumps([])


def emptySessionFormData():
    session['formSlug'] = ""
    session['formStructure'] = json.dumps([])
