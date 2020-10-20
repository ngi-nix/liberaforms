"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
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

import os, datetime, unicodecsv as csv
from urllib.parse import urlparse

from flask import g
from flask_babel import gettext

from liberaforms import app, db
from liberaforms.utils.queryset import HostnameQuerySet
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils import sanitizers
from liberaforms.utils.utils import isFutureDate

#from pprint import pprint as pp


class Form(db.Document):
    meta = {'collection': 'forms', 'queryset_class': HostnameQuerySet}
    created = db.StringField(required=True)
    hostname = db.StringField(required=True)
    slug = db.StringField(required=True)
    author_id = db.StringField(db_field="author", required=True)
    editors = db.DictField(required=True)
    postalCode = db.StringField(required=False)
    enabled = db.BooleanField()
    expired = db.BooleanField()
    sendConfirmation = db.BooleanField()
    expiryConditions = db.DictField(required=True)
    """
    structure: A list of dicts that is built by and rendered by formbuilder.
    fieldIndex: List of dictionaries. Each dict contains one formbuider field info.
                [{"label": <displayed_field_name>, "name": <unique_field_identifier>}]
    """
    structure = db.ListField(required=True)
    fieldIndex = db.ListField(required=True)
    sharedEntries = db.DictField(required=False)
    log = db.ListField(required=False)
    restrictedAccess = db.BooleanField()
    adminPreferences = db.DictField(required=True)
    introductionText = db.DictField(required=True)
    afterSubmitText = db.DictField(required=True)
    expiredText = db.DictField(required=True)
    consentTexts = db.ListField(required=False)
    site = None

    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)
        from liberaforms.models.site import Site
        self.site=Site.find(hostname=self.hostname)
   
    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)
        
    @classmethod
    def find(cls, **kwargs):
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, **kwargs):
        if 'editor_id' in kwargs:
            kwargs={"__raw__": {'editors.%s' % kwargs["editor_id"]: {'$exists': True}}, **kwargs}
            kwargs.pop('editor_id')
        if 'key' in kwargs:
            kwargs={"sharedEntries__key": kwargs['key'], **kwargs}
            kwargs.pop('key')
        return cls.objects.ensure_hostname(**kwargs)
   
    def getAuthor(self):
        from liberaforms.models.user import User
        return User.find(id=self.author_id)

    def changeAuthor(self, new_author):
        if new_author.enabled:
            if str(new_author.id) == self.author_id:
                return False
            try:
                del self.editors[self.author_id]
            except:
                return False
            self.author_id=str(new_author.id)
            if not self.isEditor(new_author):
                self.addEditor(new_author)
            self.save()
            return True
        return False

    @staticmethod
    def createFieldIndex(structure):
        index=[]
        # Add these RESERVED fields to the index.
        index.append({'label': gettext("Marked"), 'name': 'marked'})
        index.append({'label': gettext("Created"), 'name': 'created'})
        for element in structure:
            if 'name' in element:
                if 'label' not in element:
                    element['label']=gettext("Label")
                index.append({'name': element['name'], 'label': element['label']})
        return index
        
    def updateFieldIndex(self, newIndex):
        if self.getTotalEntries() == 0:
            self.fieldIndex = newIndex
        else:
            deletedFieldsWithData=[]
            # If the editor has deleted fields we want to remove them
            # but we don't want to remove fields that already contain data in the DB.
            for field in self.fieldIndex:
                if not [i for i in newIndex if i['name'] == field['name']]:
                    # This field was removed by the editor. Can we safely delete it?
                    can_delete=True
                    entries = self.getEntries()
                    for entry in entries:
                        entry_data = entry['data']
                        if field['name'] in entry_data and entry_data[field['name']]:
                            # This field contains data
                            can_delete=False
                            break
                    if can_delete:
                        # A pseudo delete. We drop the field (it's reference) from the index.
                        # Note that the empty field in each entry is not deleted from the db.
                        pass
                    else:
                        # We maintain this field in the index because it contains data
                        field['removed']=True
                        deletedFieldsWithData.append(field)
            self.fieldIndex = newIndex + deletedFieldsWithData

    def getFieldIndexForDataDisplay(self, with_deleted_columns=False):
        result=[]
        for field in self.fieldIndex:
            if 'removed' in field and not with_deleted_columns:
                continue
            item={'label': field['label'], 'name': field['name']}
            result.append(item)
        if self.dataConsent["enabled"]:
            # append dynamic DPL field
            result.append({"name": "DPL", "label": gettext("DPL")})
        return result
    
    def hasRemovedFields(self):
        return any('removed' in field for field in self.fieldIndex)

    @staticmethod
    def isEmailField(field):
        if  "type" in field and field["type"] == "text" and \
            "subtype" in field and field["subtype"] == "email":
            return True
        else:
            return False
    
    @classmethod
    def structureHasEmailField(cls, structure):
        for element in structure:
            if cls.isEmailField(element):
                return True
        return False
        
    def hasEmailField(self):
        return Form.structureHasEmailField(self.structure)

    def mightSendConfirmationEmail(self):
        if self.sendConfirmation and self.hasEmailField():
            return True
        else:
            return False
    
    def getConfirmationEmailAddress(self, entry):
        for element in self.structure:
            if Form.isEmailField(element):
                if element["name"] in entry and entry[element["name"]]:
                    return entry[element["name"]].strip()
        return False

    def getEntries(self, oldest_first=False, **kwargs):
        kwargs['oldest_first'] = oldest_first
        kwargs['form_id'] = str(self.id)
        return FormResponse.findAll(**kwargs)

    def findEntry(self, entry_id):
        return FormResponse.find(id=entry_id, form_id=str(self.id))

    def addEntry(self, data):
        if 'created'in data: # data comes from 'undo delete'
            created = data['created']
            data.pop('created')
        else:
            created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 'marked'in data: # data comes from 'undo delete'
            marked = data['marked']
            data.pop('marked')
        else:
            marked = False
        response={  'hostname': self.hostname,
                    'form_id': str(self.id),
                    'author_id': self.author_id,
                    'created': created,
                    'marked': marked,
                    'data': data }
        new_response = FormResponse(**response)
        new_response.save()
        return new_response
        
    def getEntriesForDisplay(self, oldest_first=False):
        entries = self.getEntries(oldest_first=oldest_first)
        result = []
        for entry in entries:
            result.append({ 'id': entry.id,
                            'created': entry.created,
                            'marked': entry.marked,
                            **entry.data})
        return result

    def getTotalEntries(self):
        return FormResponse.findAll(form_id=str(self.id)).count()

    def getLastEntryDate(self):
        last_entry = FormResponse.find(form_id=str(self.id))
        return last_entry.created if last_entry else "" 

    def isEnabled(self):
        if not (self.getAuthor().enabled and self.adminPreferences['public']):
            return False
        return self.enabled

    @classmethod
    def newEditorPreferences(cls, editor):
        return {'notification': {   'newEntry': editor.preferences["newEntryNotification"],
                                    'expiredForm': True }}

    def addEditor(self, editor):
        if not editor.enabled:
            return False
        editor_id=str(editor.id)
        if not editor_id in self.editors:
            self.editors[editor_id]=Form.newEditorPreferences(editor)
            self.save()
            return True
        return False

    def removeEditor(self, editor):
        editor_id=str(editor.id)
        if editor_id == self.author_id:
            return None
        if editor_id in self.editors:
            del self.editors[editor_id]
            self.save()
            return editor_id
        return None
   
    @property
    def url(self):
        return "%s%s" % (self.site.host_url, self.slug)  

    @property
    def embed_url(self):
        return "%sembed/%s" % (self.site.host_url, self.slug)

    @property
    def dataConsent(self):
        return self.consentTexts[0]
    
    def getConsentForDisplay(self, id):
        return ConsentText.getConsentForDisplay(id, self)

    def saveConsent(self, id, data):
        return ConsentText.save(id, self, data)

    def getDataConsentForDisplay(self):
        return self.getConsentForDisplay(self.dataConsent['id'])
        
    def getDefaultDataConsentForDisplay(self):
        return ConsentText.getConsentForDisplay(g.site.DPLConsentID, self.author)

    def toggleDataConsentEnabled(self):
        return ConsentText.toggleEnabled(self.dataConsent['id'], self)

    @staticmethod
    def newDataConsent():
        consent = ConsentText.getEmptyConsent(  g.site.DPLConsentID,
                                                name="DPL",
                                                enabled=g.site.dataConsent['enabled'])
        return consent

    @staticmethod
    def defaultExpiredText():
        text=gettext("Sorry, this form has expired.")
        return {"markdown": "## %s" % text, "html": "<h2>%s</h2>" % text}

    @property
    def expiredTextHTML(self):
        if self.expiredText['html']:
            return self.expiredText['html']
        else:
            return Form.defaultExpiredText()["html"]

    @property
    def expiredTextMarkdown(self):
        if self.expiredText['markdown']:
            return self.expiredText['markdown']
        else:
            return Form.defaultExpiredText()["markdown"]

    def saveExpiredText(self, markdown):
        markdown=markdown.strip()
        if markdown:
            self.expiredText = {'markdown': sanitizers.escapeMarkdown(markdown),
                                'html': sanitizers.markdown2HTML(markdown)}
        else:
            self.expiredText = {'html':"", 'markdown':""}
        self.save()

    @staticmethod
    def defaultAfterSubmitText():
        text=gettext("Thank you!!")
        return {"markdown": "## %s" % text, "html": "<h2>%s</h2>" % text}

    @property
    def afterSubmitTextHTML(self):
        if self.afterSubmitText['html']:
            return self.afterSubmitText['html']
        else:
            return Form.defaultAfterSubmitText()['html']

    @property
    def afterSubmitTextMarkdown(self):
        if self.afterSubmitText['markdown']:
            return self.afterSubmitText['markdown']
        else:
            return Form.defaultAfterSubmitText()['markdown']

    def saveAfterSubmitText(self, markdown):
        markdown=markdown.strip()
        if markdown:
            self.afterSubmitText = {'markdown': sanitizers.escapeMarkdown(markdown),
                                    'html': sanitizers.markdown2HTML(markdown)}
        else:
            self.afterSubmitText = {'html':"", 'markdown':""}
        self.save()

    def getAvailableNumberTypeFields(self):
        result={}
        for element in self.structure:
            if "type" in element and element["type"] == "number":
                if element["name"] in self.fieldConditions:
                    result[element["name"]]=self.fieldConditions[element["name"]]
                else:
                    result[element["name"]]={"type":"number", "condition": None}
        return result

    def getMultiChoiceFields(self):
        result=[]
        for element in self.structure:
            if "type" in element:
                if  element["type"] == "checkbox-group" or \
                    element["type"] == "radio-group" or \
                    element["type"] == "select":
                    result.append(element)
        return result        

    def getFieldLabel(self, fieldName):
        for element in self.structure:
            if 'name' in element and element['name']==fieldName:
                return element['label']
        return None

    @property
    def fieldConditions(self):
        return self.expiryConditions["fields"]

    def updateExpiryConditions(self):
        savedConditionalFields = [field for field in self.expiryConditions["fields"]]
        availableConditionalFields=[element["name"] for element in self.structure if "name" in element]
        for field in savedConditionalFields:
            if not field in availableConditionalFields:
                del self.expiryConditions["fields"][field]

    def getConditionalFieldPositions(self):
        conditionalFieldPositions=[]
        for fieldName, condition in self.fieldConditions.items():
            if condition['type'] == 'number':
                for position, field in enumerate(self.fieldIndex):
                    if field['name'] == fieldName:
                        conditionalFieldPositions.append(position)
                        break
        return conditionalFieldPositions

    @classmethod
    def saveNewForm(cls, formData):
        if formData['slug'] in app.config['RESERVED_SLUGS']:
            return None
        new_form=Form(**formData)
        new_form.save()
        return new_form

    def deleteForm(self):
        self.deleteEntries()
        self.delete()

    def deleteEntries(self):
        FormResponse.findAll(form_id=str(self.id)).delete()
    
    def isAuthor(self, user):
        return True if self.author_id == str(user.id) else False
        
    def isEditor(self, user):
        return True if str(user.id) in self.editors else False

    def getEditors(self):
        from liberaforms.models.user import User
        editors=[]
        for editor_id in self.editors:
            #print (editor_id)
            user=User.find(id=editor_id)
            if user:
                editors.append(user)
            else:
                # remove editor_id from self.editors
                pass
        return editors

    def canExpire(self):
        if self.expiryConditions["expireDate"]:
            return True
        if self.expiryConditions["fields"]:
            return True
        return False
    
    def hasExpired(self):
        if not self.canExpire():
            return False
        if self.expiryConditions["expireDate"] and not isFutureDate(self.expiryConditions["expireDate"]):
            return True
        for fieldName, value in self.fieldConditions.items():
            if value['type'] == 'number':
                total=self.tallyNumberField(fieldName)
                if total >= int(value['condition']):
                    return True
        return False

    def tallyNumberField(self, fieldName):
        total=0
        for entry in self.getEntries():
            try:
                total = total + int(entry[fieldName])
            except:
                continue
        return total
                
    def isPublic(self):
        if not self.isEnabled() or self.expired:
            return False
        else:
            return True

    def isShared(self):
        if self.areEntriesShared():
            return True
        if len(self.editors) > 1:
            return True
        return False
    
    def areEntriesShared(self):
        return self.sharedEntries['enabled']
    
    def getSharedEntriesURL(self, part="results"):
        return "%s/%s/%s" % (self.url, part, self.sharedEntries['key'])

    """
    Used when editing a form.
    We don't want the Editor to change the option values if an
    entry with that value is already present in the database
    """
    def getMultichoiceOptionsWithSavedData(self):
        result = {}
        entries = self.getEntries()
        if not entries:
            return result
        multiChoiceFields = {}  # {field.name: [option.value, option.value]}
        for field in self.getMultiChoiceFields():
            multiChoiceFields[field['name']] = []
            for value in field['values']:
                multiChoiceFields[field['name']].append(value['value'])
        for entry in entries:
            entry_data = entry['data']
            removeFieldsFromSearch=[]
            for field in multiChoiceFields:
                if field in entry_data.keys():
                    for savedValue in entry_data[field].split(', '):
                        if savedValue in multiChoiceFields[field]:
                            if not field in result:
                                    result[field]=[]
                            result[field].append(savedValue)
                            multiChoiceFields[field].remove(savedValue)
                            if multiChoiceFields[field] == []:  # all option.values are present in database
                                removeFieldsFromSearch.append(field)
            for field_to_remove in removeFieldsFromSearch:
                del(multiChoiceFields[field_to_remove])
                if multiChoiceFields == {}: # no more fields to check
                    return result
        return result

    #@property
    #def orderedEntries(self):
    #    return sorted(self.entries, key=lambda k: k['created'])

    def getEntriesForJSON(self):
        result=[]
        entries = self.getEntriesForDisplay(oldest_first=True)
        for saved_entry in entries:
            entry={}
            for field in self.getFieldIndexForDataDisplay():
                value=saved_entry[field['name']] if field['name'] in saved_entry else ""
                entry[field['label']]=value
            result.append(entry)
        return result
        
    def getChartData(self):
        chartable_time_fields=[]
        total={'entries':0}
        time_data={'entries':[]}
        for field in self.getAvailableNumberTypeFields():
            label=self.getFieldLabel(field)
            total[label]=0
            time_data[label]=[]
            chartable_time_fields.append({'name':field, 'label':label})
            
        multichoice_fields=self.getMultiChoiceFields()
        multi_choice_for_chart=[]
        for field in multichoice_fields:
            field_for_chart={   "name":field['name'], "title":field['label'],
                                "axis_1":[], "axis_2":[]}
            multi_choice_for_chart.append(field_for_chart)
            
            for value in field['values']:
                field_for_chart['axis_1'].append(value['label'])
                field_for_chart['axis_2'].append(0) #start counting at zero
        for entry in self.getEntriesForDisplay(oldest_first=True):
            total['entries']+=1
            time_data['entries'].append({   'x': entry['created'],
                                            'y': total['entries']})
            for field in chartable_time_fields:
                try:
                    total[field['label']]+=int(entry[field['name']])
                    time_data[field['label']].append({  'x': entry['created'],
                                                        'y': total[field['label']]})
                except:
                    continue
            for field in multichoice_fields:
                if not (field['name'] in entry and entry[field['name']]):
                    continue
                field_for_chart=[item for item in multi_choice_for_chart if item["name"]==field['name']][0]
                entry_values=entry[field['name']].split(', ')
                for idx, field_value in enumerate(field['values']):
                    if field_value['value'] in entry_values:
                        field_for_chart['axis_2'][idx]+=1
        return {'multi_choice':multi_choice_for_chart,
                'time_chart':time_data}

    def toggleEnabled(self):
        if self.expired or self.adminPreferences['public']==False:
            return False
        else:
            self.enabled = False if self.enabled else True
            self.save()
            return self.enabled
            
    def toggleAdminFormPublic(self):
        self.adminPreferences['public'] = False if self.adminPreferences['public'] else True
        self.save()
        return self.adminPreferences['public']
    
    def toggleSharedEntries(self):
        self.sharedEntries['enabled'] = False if self.sharedEntries['enabled'] else True
        self.save()
        return self.sharedEntries['enabled']

    def toggleRestrictedAccess(self):
        self.restrictedAccess = False if self.restrictedAccess else True
        self.save()
        return self.restrictedAccess
        
    def toggleNotification(self, editor_id):
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['newEntry']:
                self.editors[editor_id]['notification']['newEntry']=False
            else:
                self.editors[editor_id]['notification']['newEntry']=True
            self.save()
            return self.editors[editor_id]['notification']['newEntry']
        return False

    def toggleExpirationNotification(self, editor_id):
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['expiredForm']:
                self.editors[editor_id]['notification']['expiredForm']=False
            else:
                self.editors[editor_id]['notification']['expiredForm']=True
            self.save()
            return self.editors[editor_id]['notification']['expiredForm']
        return False
    
    def toggleSendConfirmation(self):
        self.sendConfirmation = False if self.sendConfirmation else True
        self.save()
        return self.sendConfirmation
        
    def addLog(self, message, anonymous=False):
        if anonymous:
            actor="system"
        else:
            actor=g.current_user.username if g.current_user else "system"
        logTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log.insert(0, (logTime, actor, message))
        self.save()

    def writeCSV(self, with_deleted_columns=False):
        fieldnames=[]
        fieldheaders={}
        for field in self.getFieldIndexForDataDisplay(with_deleted_columns):
            fieldnames.append(field['name'])
            fieldheaders[field['name']]=field['label']
        csv_name = os.path.join(app.config['TMP_DIR'], "{}.csv".format(self.slug))
        with open(csv_name, mode='wb') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore')
            writer.writerow(fieldheaders)
            entries = self.getEntriesForDisplay(oldest_first=True)
            for entry in entries:
                writer.writerow(entry)
        return csv_name
        
    @staticmethod
    def defaultIntroductionText():
        title=gettext("Form title")
        context=gettext("Context")
        content=gettext(" * Describe your form.\n * Add relevant content, links, images, etc.")
        return "## {}\n\n### {}\n\n{}".format(title, context, content)


class FormResponse(db.Document):
    meta = {'collection': 'responses', 'queryset_class': HostnameQuerySet}
    created = db.StringField(required=True)
    hostname = db.StringField(required=True)
    author_id = db.StringField(required=True)
    form_id = db.StringField(required=True)
    marked = db.BooleanField(default=False)
    data = db.DictField(required=False)
    
    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        from liberaforms.utils.utils import print_obj_values
        return print_obj_values(self)

    @classmethod
    def find(cls, **kwargs):
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, **kwargs):
        order = 'created' if 'oldest_first' in kwargs and kwargs['oldest_first'] else '-created'
        if 'oldest_first' in kwargs:
            kwargs.pop('oldest_first')
        return cls.objects.ensure_hostname(**kwargs).order_by(order)
