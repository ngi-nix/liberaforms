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

from flask import session
import json

def ensureSessionFormKeys():
    if not 'slug' in session:
        session['slug'] = ""
    if not 'formFieldIndex' in session:
        session['formFieldIndex'] = []
    if not 'formStructure' in session:
        session['formStructure'] = json.dumps([])
    if not 'introductionTextMD' in session:
        session['introductionTextMD'] = ''
    if not 'afterSubmitTextMD' in session:
        session['afterSubmitTextMD'] = ''
        
def populateSessionFormData(form):
    #session['form_id'] = str(form._id)
    session['slug'] = form.slug
    session['formFieldIndex'] = form.fieldIndex
    session['formStructure'] = form.structure
    session['introductionTextMD'] = form.introductionText['markdown']
    session['afterSubmitTextMD'] = form.afterSubmitText['markdown']

def clearSessionFormData():
    session['slug'] = ""
    session['form_id']=None
    session['formFieldIndex'] = []
    session['formStructure'] = json.dumps([])
    session['introductionTextMD'] = ''
    session['afterSubmitTextMD'] = ''
