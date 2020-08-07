"""
“Copyright 2020 La Coordinadora d’Entitats per la Lleialtat Santsenca”

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

from flask import flash, request, g
from flask_babel import gettext 
from urllib.parse import urlparse
import os, string, random, datetime, json, markdown, csv
from mongoengine import QuerySet

from gngforms import app, db
from gngforms.utils.utils import *
from gngforms.utils.migrate import migrateMongoSchema

#from pprint import pprint as pp


class HostnameQuerySet(QuerySet):
    def ensure_hostname(self, **kwargs):
        if not g.isRootUserEnabled and not 'hostname' in kwargs:
            kwargs={'hostname':g.site.hostname, **kwargs}
        #print("ensure_hostname kwargs: %s" % kwargs)
        return self.filter(**kwargs)


class User(db.Document):
    meta = {'collection': 'users', 'queryset_class': HostnameQuerySet}
    username = db.StringField(required=True)
    email = db.StringField(required=True)
    password_hash =db.StringField(db_field="password", required=True)
    hostname = db.StringField(required=True)
    preferences = db.DictField(required=False)
    blocked = db.BooleanField()
    admin = db.DictField(required=True)
    validatedEmail = db.BooleanField()
    created = db.StringField(required=True)
    token = db.DictField(required=False)
    
    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        return pformat({'User': get_obj_values_as_dict(self)})
    
    @classmethod
    def create(cls, newUserData):
        newUser=User(**newUserData)
        newUser.save()
        return newUser

    @classmethod
    def find(cls, **kwargs):
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, *args, **kwargs):
        if 'token' in kwargs:
            kwargs={"token__token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        return cls.objects.ensure_hostname(**kwargs)
    
    @property
    def enabled(self):
        if not self.validatedEmail:
            return False
        if self.blocked:
            return False
        return True

    @property
    def forms(self):
        return Form.findAll(editor_id=str(self.id))

    @property
    def authored_forms(self):
        return Form.findAll(author_id=str(self.id))
        
    @property
    def language(self):
        return self.preferences["language"]

    @property
    def newEntryNotificationDefault(self):
        return self.preferences["newEntryNotification"]

    def isAdmin(self):
        return True if self.admin['isAdmin']==True else False

    def isRootUser(self):
        return True if self.email in app.config['ROOT_USERS'] else False
    
    def verifyPassword(self, password):
        return verifyPassword(password, self.password_hash)
        
    def deleteUser(self):
        forms = Form.findAll(author_id=str(self.id))
        for form in forms:
            form.delete()
        forms = Form.findAll(editor_id=str(self.id))
        for form in forms:
            del form.editors[str(self.id)]
            form.save()
        self.delete()
    
    def setToken(self, **kwargs):
        self.token=createToken(User, **kwargs)
        self.save()

    def deleteToken(self):
        self.token={}
        self.save()

    def toggleBlocked(self):
        if self.isRootUser():
            self.blocked=False
        else:
            self.blocked=False if self.blocked else True
        self.save()
        return self.blocked

    def toggleNewEntryNotificationDefault(self):
        if self.preferences["newEntryNotification"]==True:
            self.preferences["newEntryNotification"]=False
        else:
            self.preferences["newEntryNotification"]=True
        self.save()
        return self.preferences["newEntryNotification"]

    def toggleAdmin(self):
        if self.isRootUser():
            return self.isAdmin()
        self.admin['isAdmin']=False if self.isAdmin() else True
        self.save()
        return self.isAdmin()

    @staticmethod
    def defaultAdminSettings():
        return {
            "isAdmin": False,
            "notifyNewUser": False,
            "notifyNewForm": False
        }

    """
    send this admin an email when a new user registers at the site
    """
    def toggleNewUserNotification(self):
        if not self.isAdmin():
            return False
        self.admin['notifyNewUser']=False if self.admin['notifyNewUser'] else True
        self.save()
        return self.admin['notifyNewUser']

    """
    send this admin an email when a new form is created
    """
    def toggleNewFormNotification(self):
        if not self.isAdmin():
            return False
        self.admin['notifyNewForm']=False if self.admin['notifyNewForm'] else True
        self.save()
        return self.admin['notifyNewForm']    

    def canInspectForm(self, form):
        return True if (str(self.id) in form.editors or self.isAdmin()) else False
    

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
    structure: A list of dicts that is rendered by formbuilder
    fieldIndex: List of dictionaries. Each dict contains one field.
                [{"label": <visible_field_name>, "name": <unique_field_identifier>}]
    entries: List of dictionaries containing the data submitted by visitors.
                [{unique_field_identifier: value, unique_field_identifier: value}]
    """
    structure = db.ListField(required=True)
    fieldIndex = db.ListField(required=True)
    entries = db.ListField(required=False)
    sharedEntries = db.DictField(required=False)
    log = db.ListField(required=False)
    restrictedAccess = db.BooleanField()
    adminPreferences = db.DictField(required=True)
    introductionText = db.DictField(required=True)
    afterSubmitText = db.DictField(required=True)
    expiredText = db.DictField(required=True)
    dataConsent = db.DictField(required=True)
    site = None

    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)
        self.site=Site.find(hostname=self.hostname)
   
    def __str__(self):
        return pformat({'Form': get_obj_values_as_dict(self)})
        
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

    @property
    def user(self):
        return self.author
        
    @property
    def author(self):
        return User.find(id=self.author_id)

    def changeAuthor(self, new_author):
        if new_author.enabled:
            if new_author == self.author:
                return False
            if self.isEditor(self.author):
                del self.editors[self.author_id]
            else:
                return False # this should never happen
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
        if self.totalEntries == 0:
            self.fieldIndex = newIndex
        else:
            deletedFieldsWithData=[]
            # If the editor has deleted fields we want to remove them
            # but we don't want to remove fields that already contain data in the DB.
            for field in self.fieldIndex:
                if not [i for i in newIndex if i['name'] == field['name']]:
                    # This field was removed by the editor. Can we safely delete it?
                    can_delete=True
                    for entry in self.entries:
                        if field['name'] in entry and entry[field['name']]:
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
        if self.isDataConsentRequired():
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
        for element in self.structure: #json.loads(self.structure):
            if Form.isEmailField(element):
                if element["name"] in entry and entry[element["name"]]:
                    return entry[element["name"]].strip()
        return False

    @property
    def totalEntries(self):
        return len(self.entries)

    def isEnabled(self):
        if not (self.author.enabled and self.adminPreferences['public']):
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

    def removeEditor(self, editor_id):
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

    def isDataConsentEnabled(self):
        return self.isDataConsentRequired()

    def isDataConsentRequired(self):
        return self.dataConsent["required"]
    
    @property
    def dataConsentHTML(self):
        if self.dataConsent['html']:
            return self.dataConsent['html']
        if self.site.isPersonalDataConsentEnabled() and self.site.personalDataConsent['html']:
            return self.site.personalDataConsent['html']
        return Installation.fallbackDPL()["html"]

    @property
    def dataConsentMarkdown(self):
        if self.dataConsent['markdown']:
            return self.dataConsent['markdown']
        if self.site.isPersonalDataConsentEnabled() and self.site.personalDataConsent['markdown']:
            return self.site.personalDataConsent['markdown']
        return Installation.fallbackDPL()["markdown"]       

    def saveDataConsentText(self, markdown):
        markdown=markdown.strip()
        if markdown:
            self.dataConsent = {'markdown':escapeMarkdown(markdown),
                                'html':markdown2HTML(markdown),
                                'required': self.dataConsent['required']}
        else:
            self.dataConsent = {'html':"", 'markdown':"", 'required':self.dataConsent['required']}
        self.save()

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
            self.expiredText = {'markdown':escapeMarkdown(markdown),
                                'html':markdown2HTML(markdown)}
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
            self.afterSubmitText = {'markdown':escapeMarkdown(markdown),
                                    'html':markdown2HTML(markdown)}
        else:
            self.afterSubmitText = {'html':"", 'markdown':""}
        self.save()

    @property
    def lastEntryDate(self):
        if self.entries:
            last_entry = self.entries[-1] 
            return last_entry["created"]
        else:
            return ""

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

    def deleteEntries(self):
        self.entries=[]
        self.save()
    
    def isAuthor(self, user):
        return True if self.author_id == user.id else False
        
    def isEditor(self, user):
        return True if str(user.id) in self.editors else False

    def getEditors(self):
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
        for entry in self.entries:
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

    @property
    def orderedEntries(self):
        return sorted(self.entries, key=lambda k: k['created'])

    def getEntriesForJSON(self):
        result=[]
        for saved_entry in self.orderedEntries:
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
        multi_choice_data={}
        for field in multichoice_fields:
            multi_choice_data[field['label']]={}
            multi_choice_data[field['label']]['axis_1']=[]
            multi_choice_data[field['label']]['axis_2']=[]
            for value in field['values']:
                label=value['label']
                if len(label) > 24:
                    # a shorter label length to fit inside jcharts multi-option divs
                    label=label[:22]+'..'
                multi_choice_data[field['label']]['axis_1'].append(label)
                multi_choice_data[field['label']]['axis_2'].append(0) #start counting at zero

        for entry in self.orderedEntries:
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
                entry_values=entry[field['name']].split(', ')
                for idx, field_value in enumerate(field['values']):
                    if field_value['value'] in entry_values:
                        multi_choice_data[field['label']]['axis_2'][idx]+=1
        result={}
        result['multi_choice']=multi_choice_data
        result['time_chart']=time_data
        return result

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
        
    def toggleNotification(self):
        editor_id=str(g.current_user.id)
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['newEntry']:
                self.editors[editor_id]['notification']['newEntry']=False
            else:
                self.editors[editor_id]['notification']['newEntry']=True
            self.save()
            return self.editors[editor_id]['notification']['newEntry']
        return False

    def toggleExpirationNotification(self):
        editor_id=str(g.current_user.id)
        if editor_id in self.editors:
            if self.editors[editor_id]['notification']['expiredForm']:
                self.editors[editor_id]['notification']['expiredForm']=False
            else:
                self.editors[editor_id]['notification']['expiredForm']=True
            self.save()
            return self.editors[editor_id]['notification']['expiredForm']
        return False

    def toggleRequireDataConsent(self):
        self.dataConsent["required"] = False if self.dataConsent["required"] else True
        self.save()
        return self.dataConsent["required"]

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
        csv_name='%s/%s.csv' % (app.config['TMP_DIR'], self.slug)
        with open(csv_name, mode='w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore')
            writer.writerow(fieldheaders)
            for entry in self.orderedEntries:
                writer.writerow(entry)
        return csv_name
        
    @staticmethod
    def defaultIntroductionText():
        title=gettext("Form title")
        context=gettext("Context")
        content=gettext(" * Describe your form.\n * Add relevant content, links, images, etc.")
        return "## {}\n\n### {}\n\n{}".format(title, context, content)


class Site(db.Document):
    meta = {'collection': 'sites', 'queryset_class': HostnameQuerySet}
    hostname = db.StringField(required=True)
    port = db.StringField(required=False)
    siteName = db.StringField(required=True)
    defaultLanguage=db.StringField(required=True)
    menuColor=db.StringField(required=True)
    scheme = db.StringField(required=False)
    blurb = db.DictField(required=True)
    termsAndConditions = db.DictField(required=True)
    invitationOnly = db.BooleanField()
    personalDataConsent = db.DictField(required=False)
    smtpConfig = db.DictField(required=True)

    def __init__(self, *args, **kwargs):        
        db.Document.__init__(self, *args, **kwargs)
    
    def __str__(self):
        return pformat({'Site': get_obj_values_as_dict(self)})
    
    @classmethod
    def create(cls):
        hostname=urlparse(request.host_url).hostname
        with open('%s/default_blurb.md' % os.path.dirname(os.path.realpath(__file__)), 'r') as defaultBlurb:
            defaultMD=defaultBlurb.read()
        blurb = {
            'markdown': defaultMD,
            'html': markdown.markdown(defaultMD)
        }
        newSiteData={
            "hostname": hostname,
            "port": None,
            "scheme": urlparse(request.host_url).scheme,
            "blurb": blurb,
            "invitationOnly": True,
            "siteName": "GNGforms!",
            "defaultLanguage": app.config['DEFAULT_LANGUAGE'],
            "menuColor": "#b71c1c",
            "personalDataConsent": {"markdown": "", "html": "", "enabled": False },
            "termsAndConditions": {"markdown": "", "html": "", "enabled": False},
            "smtpConfig": {
                "host": "smtp.%s" % hostname,
                "port": 25,
                "encryption": "",
                "user": "",
                "password": "",
                "noreplyAddress": "no-reply@%s" % hostname
            }
        }
        new_site=Site(**newSiteData)
        new_site.save()
        #create the Installation if it doesn't exist
        Installation.get()
        return new_site

    @classmethod
    def find(cls, *args, **kwargs):
        site = cls.findAll(*args, **kwargs).first()
        if not site:
            site=Site.create()
        return site

    @classmethod
    def findAll(cls, *args, **kwargs):
        return cls.objects.ensure_hostname(**kwargs)

    @property
    def host_url(self):
        url= "%s://%s" % (self.scheme, self.hostname)
        if self.port:
            url = "%s:%s" % (url, self.port)
        return url+'/'

    def faviconURL(self):
        path="%s%s_favicon.png" % (app.config['FAVICON_FOLDER'], self.hostname)
        if os.path.exists(path):
            return "/static/images/favicon/%s_favicon.png" % self.hostname
        else:
            return "/static/images/favicon/default-favicon.png"

    def deleteFavicon(self):
        path="%s%s_favicon.png" % (app.config['FAVICON_FOLDER'], self.hostname)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def saveBlurb(self, MDtext):
        self.blurb = {'markdown':escapeMarkdown(MDtext), 'html':markdown2HTML(MDtext)}
        self.save()

    def savePersonalDataConsentText(self, MDtext):
        self.personalDataConsent = {'markdown':escapeMarkdown(MDtext),
                                    'html':markdown2HTML(MDtext),
                                    'enabled': self.personalDataConsent['enabled']}
        self.save()

    @property
    def termsAndConditionsHTML(self):
        return self.termsAndConditions['html']

    @property
    def termsAndConditionsMarkdown(self):
        return self.termsAndConditions['markdown']

    def saveTermsAndConditions(self, markdown):
        markdown=markdown.strip()
        if markdown:
            self.termsAndConditions = { 'markdown':escapeMarkdown(markdown),
                                        'html':markdown2HTML(markdown),
                                        'enabled': self.termsAndConditions['enabled']}
        else:
            self.termsAndConditions = { 'markdown': "", 'html': "",
                                        'enabled': self.termsAndConditions['enabled']}
        self.save()

    def toggleTermsAndConditions(self):
        self.termsAndConditions['enabled'] = False if self.termsAndConditions['enabled'] else True
        self.save()
        return self.termsAndConditions['enabled']


    def isPersonalDataConsentEnabled(self):
        return self.personalDataConsent["enabled"]
        
    @property
    def personalDataConsentHTML(self):
        return self.personalDataConsent["html"]

    @property
    def personalDataConsentMarkdown(self):
        return self.personalDataConsent["markdown"]

    def togglePersonalDataConsentEnabled(self):
        self.personalDataConsent["enabled"] = False if self.personalDataConsent["enabled"] else True
        self.save()
        return self.personalDataConsent["enabled"]

    def saveSMTPconfig(self, **kwargs):
        self.smtpConfig=kwargs
        self.save()
                
    @property
    def totalUsers(self):
        return User.findAll(hostname=self.hostname).count()

    @property
    def admins(self):
        return User.findAll(admin__isAdmin=True, hostname=self.hostname)
    
    @property
    def totalForms(self):
        return Form.findAll(hostname=self.hostname).count()
    
    def toggleInvitationOnly(self):
        self.invitationOnly = False if self.invitationOnly else True
        self.save()
        return self.invitationOnly

    def toggleScheme(self):
        self.scheme = 'https' if self.scheme=='http' else 'http'
        self.save()
        return self.scheme

    def deleteSite(self):
        users=User.findAll(hostname=self.hostname)
        for user in users:
            user.deleteUser()
        invites = Invite.findAll(hostname=self.hostname)
        for invite in invites:
            invite.delete()
        return self.delete()


class Invite(db.Document):
    meta = {'collection': 'invites', 'queryset_class': HostnameQuerySet}
    hostname = db.StringField(required=True)
    email = db.EmailField(required=True)
    message = db.StringField(required=False)
    token = db.DictField(required=True)
    admin = db.BooleanField()
   
    def __init__(self, *args, **kwargs):        
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        return pformat({'Invite': get_obj_values_as_dict(self)})

    @classmethod
    def create(cls, hostname, email, message, admin=False):
        data={
            "hostname": hostname,
            "email": email,
            "message": message,
            "token": createToken(Invite),
            "admin": admin
        }
        newInvite=Invite(**data)
        newInvite.save()
        return newInvite

    @classmethod
    def find(cls, **kwargs):
        if 'token' in kwargs:
            kwargs={"token__token": kwargs['token'], **kwargs}
            kwargs.pop('token')
        return cls.findAll(**kwargs).first()

    @classmethod
    def findAll(cls, **kwargs):
        return cls.objects.ensure_hostname(**kwargs)
    
    @property
    def link(self):
        return "{}user/new/{}".format(Site.find(hostname=self.hostname).host_url, self.token['token'])
    
    def getMessage(self):
        return "{}\n\n{}".format(self.message, self.link)

    def setToken(self, **kwargs):
        self.invite['token']=createToken(Invite, **kwargs)
        self.save()
        

class Installation(db.Document):
    name = db.StringField(required=True)
    schemaVersion = db.IntField(required=True)
    created = db.StringField(required=True)
   
    def __init__(self, *args, **kwargs):
        db.Document.__init__(self, *args, **kwargs)

    def __str__(self):
        return pformat({'Installation': get_obj_values_as_dict(self)})

    @classmethod
    def get(cls):
        installation=cls.objects.first()
        if not installation:
            installation=Installation.create()
        return installation
    
    @classmethod
    def create(cls):
        if cls.objects.first():
            return
        data={  "name": "GNGforms",
                "schemaVersion": app.config['SCHEMA_VERSION'],
                "created": datetime.date.today().strftime("%Y-%m-%d")}
        new_installation=cls(**data)
        new_installation.save()
        return new_installation
    
    def isSchemaUpToDate(self):
        return True if self.schemaVersion == app.config['SCHEMA_VERSION'] else False

    def updateSchema(self):
        if not self.isSchemaUpToDate():
            migrated_up_to=migrateMongoSchema(self.schemaVersion)
            self.schemaVersion=migrated_up_to
            self.save()
            return True if self.isSchemaUpToDate() else False
        else:
            True
    
    @staticmethod
    def isUser(email):
        return True if User.objects(email=email).first() else False
        
    @staticmethod
    def fallbackDPL():
        text=gettext("We take your data protection seriously. Please contact us for any inquiries.")
        return {"markdown": text, "html": "<p>"+text+"</p>", "enabled": False}
