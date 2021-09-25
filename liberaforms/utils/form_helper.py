"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import json
from flask import session, current_app
from flask_babel import gettext as _
from liberaforms.utils import sanitizers
from liberaforms.models.form import Form
from liberaforms.utils import utils


def clear_session_form_data():
    session['duplication_in_progress'] = False
    session['slug'] = ""
    session['form_id']=None
    session['formFieldIndex'] = []
    session['formStructure'] = json.dumps([])
    session['introductionTextMD'] = ''
    session['consentTexts'] = []
    session['afterSubmitText']= {}
    session['expiredText'] = {}

def populate_session_with_form(form):
    clear_session_form_data()
    session['slug'] = form.slug
    session['form_id'] = str(form.id)
    session['formFieldIndex'] = form.fieldIndex
    session['formStructure'] = form.structure
    session['introductionTextMD'] = form.introductionText['markdown']
    session['consentTexts'] = form.consentTexts
    session['afterSubmitText'] = form.afterSubmitText
    session['expiredText'] = form.expiredText

"""
formbuilder has some bugs.
Repair if needed.
"""
def repair_form_structure(structure):
    for element in structure:
        if "type" in element:
            if element['type'] == 'paragraph':
                # remove unwanted HTML from paragraph text (not really a bug)
                element["label"]=sanitizers.clean_label(element["label"])
                continue
            # Ensure a label without HTML tags
            if 'label' in element:
                element['label'] = sanitizers.strip_html_tags(element['label']).strip()
                element['label'] = sanitizers.remove_newlines(element['label'])
            if not 'label' in element or element['label']=="":
                element['label']=_("Label")
            # formBuilder does not save select dropdown correctly
            if element["type"] == "select" and "multiple" in element:
                if element["multiple"] == False:
                    del element["multiple"]
            # formBuilder does not enforce values for checkbox groups, radio groups and selects.
            # we add a random value when missing
            if  element["type"] == "checkbox-group" or \
                element["type"] == "radio-group" or \
                element["type"] == "select":
                for input_option in element["values"]:
                    if not input_option["value"]:
                        input_option["value"] = utils.gen_random_string()
    return structure

def is_slug_available(slug):
    if Form.find(slug=slug):
        return False
    if slug in current_app.config['RESERVED_SLUGS']:
        return False
    return True
