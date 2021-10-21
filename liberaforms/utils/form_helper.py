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
def repair_form_structure(structure, form=None):
    def get_unique_option_value(values, label):
        value = label.replace(" ", "-")
        value = sanitizers.sanitize_string(value)
        value = sanitizers.strip_html_tags(value)
        value = sanitizers.remove_newlines(value)
        if len(value) > 43:
            value = f"{value[:40]}..." # make value length 43 chars
        unique_values=[option["value"] for option in values if option["value"]]
        cnt = 1
        while value in unique_values:
            value = f"{value}.{cnt}"
            cnt = cnt + 1
        return value
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
            # we add a value (derived form the Label) when missing
            if  element["type"] == "checkbox-group" or \
                element["type"] == "radio-group" or \
                element["type"] == "select":
                options = []
                for option in element["values"]:
                    option["value"] = option["value"].strip()
                    if not option["label"] and not option["value"]:
                        continue
                    if not option["label"] and option["value"]:
                        option["label"] = option["value"]
                        options.append(option)
                        continue
                    if not form or form.is_public() == False:
                        if form:
                            saved_values=form.get_multichoice_options_with_saved_data()
                            if element["name"] in saved_values.keys():
                                if option["value"] in saved_values[element['name']]:
                                    options.append(option)
                                    continue
                        option["value"]=get_unique_option_value(element["values"],
                                                                option["label"])
                    options.append(option)
                element["values"] = options
    return structure

def is_slug_available(slug):
    if Form.find(slug=slug):
        return False
    if slug in current_app.config['RESERVED_SLUGS']:
        return False
    return True
