"""
“Copyright 2020 GNGforms.org”

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

import json
from flask import session
from gngforms.utils.utils import *

def clearSessionFormData():
    session['duplication_in_progress'] = False
    session['slug'] = ""
    session['form_id']=None
    session['formFieldIndex'] = []
    session['formStructure'] = json.dumps([])
    session['introductionTextMD'] = ''
    session['dataConsent'] = {}
    session['afterSubmitText']= {}
    session['expiredText'] = {}
    
def populateSessionWithForm(form):
    clearSessionFormData()
    session['slug'] = form.slug
    session['form_id'] = str(form.id)
    session['formFieldIndex'] = form.fieldIndex
    session['formStructure'] = form.structure
    session['introductionTextMD'] = form.introductionText['markdown']
    session['dataConsent'] = form.dataConsent
    session['afterSubmitText'] = form.afterSubmitText
    session['expiredText'] = form.expiredText

"""
formbuilder has some bugs.
Repair if needed.
"""
def repairFormStructure(structure):
    for element in structure:
        if "type" in element:
            if element['type'] == 'paragraph':
                # remove unwanted HTML from paragraph text (not really a bug)
                element["label"]=cleanLabel(element["label"])
                continue
            # Ensure a label without HTML tags
            if 'label' in element:
                element['label']=stripHTMLTags(element['label']).strip()
                element['label'] = removeNewLines(element['label'])
            if not 'label' in element or element['label']=="":
                element['label']=gettext("Label")                
            # formBuilder does not save select dropdown correctly
            if element["type"] == "select" and "multiple" in element:
                if element["multiple"] == False:
                    del element["multiple"]
            # formBuilder does not enforce values for checkbox groups, radio groups and selects.
            # we add a value when missing, and sanitize values (eg. a comma would be bad).
            if  element["type"] == "checkbox-group" or \
                element["type"] == "radio-group" or \
                element["type"] == "select":
                for input_type in element["values"]:
                    if not input_type["value"] and input_type["label"]:
                        input_type["value"] = input_type["label"]
                    input_type["value"] = sanitizeString(input_type["value"].replace(" ", "-"))
                    input_type["value"] = removeNewLines(input_type["value"])
    return structure
