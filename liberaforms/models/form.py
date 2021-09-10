"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, re, shutil
from datetime import datetime, timezone
import unicodecsv as csv

from flask import current_app, g
from flask_babel import gettext as _

from liberaforms import db
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TIMESTAMP
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm.attributes import flag_modified
from liberaforms.utils.database import CRUD
from liberaforms.models.formuser import FormUser
from liberaforms.models.log import FormLog
from liberaforms.models.answer import Answer, AnswerAttachment
from liberaforms.utils.storage.remote import RemoteStorage
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils import sanitizers
from liberaforms.utils import validators
from liberaforms.utils import html_parser
from liberaforms.utils import utils

from pprint import pprint

""" Form properties
structure: A list of dicts that is built by and rendered by formbuilder.
fieldIndex: List of dictionaries. Each dict contains one formbuider field info.
            [{"label": <displayed_field_name>, "name": <unique_field_identifier>}]
"""
class Form(db.Model, CRUD):
    __tablename__ = "forms"
    _site=None
    id = db.Column(db.Integer, primary_key=True, index=True)
    created = db.Column(TIMESTAMP, nullable=False)
    slug = db.Column(db.String, unique=True, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    structure = db.Column(MutableList.as_mutable(ARRAY(JSONB)), nullable=False)
    fieldIndex = db.Column(MutableList.as_mutable(ARRAY(JSONB)), nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    expired = db.Column(db.Boolean, default=False)
    sendConfirmation = db.Column(db.Boolean, default=False)
    expiryConditions = db.Column(JSONB, nullable=False)
    shared_notifications = db.Column(MutableList.as_mutable(ARRAY(db.String)), nullable=False)
    restrictedAccess = db.Column(db.Boolean, default=False)
    adminPreferences = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    introductionText = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    afterSubmitText = db.Column(JSONB, nullable=False)
    expiredText = db.Column(JSONB, nullable=False)
    thumbnail = db.Column(db.String, nullable=True)
    published_cnt = db.Column(db.Integer, default=0, nullable=False)
    consentTexts = db.Column(ARRAY(JSONB), nullable=True)
    author = db.relationship("User", back_populates="authored_forms")
    answers = db.relationship("Answer", lazy='dynamic',
                                        cascade="all, delete, delete-orphan")
    log = db.relationship("FormLog", lazy='dynamic',
                                     cascade="all, delete, delete-orphan")
    users = db.relationship("FormUser", lazy='dynamic',
                                        cascade="all, delete, delete-orphan")


    def __init__(self, author, **kwargs):
        self.created = datetime.now(timezone.utc)
        self.author_id = author.id
        self.expiryConditions = {"totalAnswers": 0,
                                 "expireDate": False,
                                 "fields": {}}
        self.slug = kwargs["slug"]
        self.structure = kwargs["structure"]
        self.fieldIndex = kwargs["fieldIndex"]
        self.shared_notifications = []
        self.introductionText = kwargs["introductionText"]
        self.consentTexts = kwargs["consentTexts"]
        self.afterSubmitText = kwargs["afterSubmitText"]
        self.expiredText = kwargs["expiredText"]
        self.sendConfirmation = self.structure_has_email_field(self.structure)
        self.adminPreferences = {"public": True}

    def __str__(self):
        return utils.print_obj_values(self)

    @property
    def site(self):
        if self._site:
            return self._site
        from liberaforms.models.site import Site
        self._site = Site.query.first()
        return self._site

    @classmethod
    def find(cls, **kwargs):
        return cls.find_all(**kwargs).first()

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def find_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs)
        #filters = []
        #filters.append(cls.editors.has_key(str(kwargs['editor_id'])))
        #filters.append(cls.sharedAnswers.contains({'key': kwargs['key']}))
        #return cls.query.filter(*filters)

    def get_author(self):
        return self.author

    def get_form_user(self, user_id):
        return FormUser.find(form_id=self.id, user_id=user_id)

    def get_created_date(self):
        return utils.utc_to_g_timezone(self.created).strftime("%Y-%m-%d")

    def change_author(self, new_author):
        if new_author.id == self.author_id:
            return False
        if not new_author.enabled:
            return False
        form_user = FormUser.find(form_id=self.id, user_id=new_author.id)
        if form_user:
            form_user.is_editor=True
            form_user.save()
        else:
            form_user=FormUser(form_id=self.id,
                               user_id=new_author.id,
                               notifications=new_author.new_form_notifications(),
                               is_editor=True)
            form_user.save()
        self.author_id=new_author.id
        self.save()
        return True

    @staticmethod
    def create_field_index(structure):
        index=[]
        # Add these RESERVED fields to the index.
        # i18n: Column title on table, to sort whether the form entries are marked or not
        index.append({'label': _("Marked"), 'name': 'marked'})
        # i18n: Used for sort items by creation order, almost always as column title
        index.append({'label': _("Created"), 'name': 'created'})
        for element in structure:
            if 'name' in element:
                if 'label' not in element:
                    element['label']=_("Label")
                index.append({'name': element['name'], 'label': element['label']})
        return index

    def update_field_index(self, newIndex):
        if self.get_total_answers() == 0:
            self.fieldIndex = newIndex
        else:
            deletedFieldsWithData=[]
            # If the editor has deleted fields we want to remove them
            # but we don't want to remove fields that already contain data in the DB.
            for field in self.fieldIndex:
                if not [i for i in newIndex if i['name'] == field['name']]:
                    # This field was removed by the editor. Can we safely delete it?
                    can_delete=True
                    for answer in self.answers:
                        if field['name'] in answer.data and \
                            answer.data[field['name']]:
                            # This field contains data
                            can_delete=False
                            break
                    if can_delete:
                        # A pseudo delete.
                        # We drop the field (it's reference) from the index
                        # (the empty field remains as is in each answer in the db)
                        pass
                    else:
                        # We don't delete this field from the index because it contains data
                        field['removed']=True
                        deletedFieldsWithData.append(field)
            self.fieldIndex = newIndex + deletedFieldsWithData

    def get_field_index_for_data_display(self, with_deleted_columns=False):
        result=[]
        for field in self.fieldIndex:
            if 'removed' in field and not with_deleted_columns:
                continue
            item={'label': field['label'], 'name': field['name']}
            result.append(item)
        if self.data_consent["enabled"]:
            # append dynamic DPL field
            # i18n: Acronym for 'Data Privacy Law'
            result.append({"name": "DPL", "label": _("DPL")})
        return result

    def has_removed_fields(self):
        return any('removed' in field for field in self.fieldIndex)

    @staticmethod
    def is_email_field(field):
        if  "type" in field and field["type"] == "text" and \
            "subtype" in field and field["subtype"] == "email":
            return True
        else:
            return False

    @classmethod
    def structure_has_email_field(cls, structure):
        for element in structure:
            if cls.is_email_field(element):
                return True
        return False

    def has_email_field(self):
        return Form.structure_has_email_field(self.structure)

    def has_field(self, field_name):
        for field in self.structure:
            if "name" in field and field["name"] == field_name:
                return True
        return False

    def has_file_field(self):
        for field in self.structure:
            if "type" in field and field["type"] == "file":
                return True
        return False

    def might_send_confirmation_email(self):
        if self.sendConfirmation and self.has_email_field():
            return True
        else:
            return False

    def get_confirmation_email_address(self, answer):
        for element in self.structure:
            if Form.is_email_field(element):
                if element["name"] in answer.data and answer.data[element["name"]]:
                    return answer.data[element["name"]].strip()
        return False

    def get_answers(self, oldest_first=False, **kwargs):
        kwargs['oldest_first'] = oldest_first
        kwargs['form_id'] = self.id
        return Answer.find_all(**kwargs)

    def get_answers_for_display(self, oldest_first=False):
        answers = self.get_answers(oldest_first=oldest_first)
        result = []
        frmt = "%Y-%m-%d %H:%M:%S"
        for answer in answers:
            result.append({
                        'id': answer.id,
                        'created': utils.utc_to_g_timezone(answer.created)
                                        .strftime(frmt),
                        'marked': answer.marked,
                        **answer.data})
        return result

    def get_total_answers(self):
        return self.answers.count()

    def get_last_answer_date(self):
        last_answer = Answer.find(form_id=self.id)
        if last_answer:
            frmt = "%Y-%m-%d %H:%M:%S"
            return utils.utc_to_g_timezone(last_answer.created).strftime(frmt)
        return ""

    def is_enabled(self):
        if not (self.get_author().enabled and self.adminPreferences['public']):
            return False
        return self.enabled

    @property
    def url(self):
        return f"{self.site.host_url}{self.slug}"

    @property
    def embed_url(self):
        return f"{self.site.host_url}embed/{self.slug}"

    def get_opengraph(self):
        default_img_src = self.site.get_logo_uri()
        image_src = self.thumbnail if self.thumbnail else default_img_src
        opengraph = {
            "title": self.slug,
            "url": self.url,
            "image": image_src,
            "description": self.get_short_description(),
        }
        return opengraph

    def set_thumbnail(self):
        html = self.introductionText['html']
        images_src = html_parser.extract_images_src(html)
        self.thumbnail = images_src[0] if images_src else None

    def set_short_description(self):
        text = html_parser.get_opengraph_text(self.introductionText['html'])
        self.introductionText['short_text'] = text

    def get_short_description(self):
        if 'short_text' in self.introductionText:
            return self.introductionText['short_text']
        self.set_short_description()
        self.save()
        return self.introductionText['short_text']

    @property
    def data_consent(self):
        return self.consentTexts[0]

    def get_consent_for_display(self, id):
        #print(self.consentTexts)
        return ConsentText.get_consent_for_display(id, self)

    def save_consent(self, id, data):
        return ConsentText.save(id, self, data)

    def get_data_consent_for_display(self):
        return self.get_consent_for_display(self.data_consent['id'])

    def get_default_data_consent_for_display(self):
        return ConsentText.get_consent_for_display( g.site.DPL_consent_id,
                                                    self.author)

    def toggle_data_consent_enabled(self):
        return ConsentText.toggle_enabled(self.data_consent['id'], self)

    @staticmethod
    def new_data_consent():
        consent = ConsentText.get_empty_consent(
                                        g.site.DPL_consent_id,
                                        name="DPL",
                                        enabled=g.site.data_consent['enabled'])
        return consent

    @staticmethod
    def default_expired_text():
        text=_("Sorry, this form has expired.")
        return {"markdown": f"## {text}", "html": f"<h2>{text}</h2>"}

    @property
    def expired_text_html(self):
        if self.expiredText['html']:
            return self.expiredText['html']
        else:
            return Form.default_expired_text()["html"]

    @property
    def expired_text_markdown(self):
        if self.expiredText['markdown']:
            return self.expiredText['markdown']
        else:
            return Form.default_expired_text()["markdown"]

    def save_expired_text(self, markdown):
        markdown=markdown.strip()
        if markdown:
            self.expiredText = {'markdown': sanitizers.escape_markdown(markdown),
                                'html': sanitizers.markdown2HTML(markdown)}
        else:
            self.expiredText = {'html':"", 'markdown':""}
        self.save()

    @staticmethod
    def defaultAfterSubmitText():
        # i18n: Thanks text displayed when completing form as user
        text=_("Thank you!!")
        return {"markdown": f"## {text}", "html": f"<h2>{text}</h2>"}

    @property
    def after_submit_text_html(self):
        if self.afterSubmitText['html']:
            return self.afterSubmitText['html']
        else:
            return Form.defaultAfterSubmitText()['html']

    @property
    def after_submit_text_markdown(self):
        if self.afterSubmitText['markdown']:
            return self.afterSubmitText['markdown']
        else:
            return Form.defaultAfterSubmitText()['markdown']

    def save_after_submit_text(self, markdown):
        markdown=markdown.strip()
        if markdown:
            self.afterSubmitText = {'markdown': sanitizers.escape_markdown(markdown),
                                    'html': sanitizers.markdown2HTML(markdown)}
        else:
            self.afterSubmitText = {'html':"", 'markdown':""}
        self.save()

    def get_available_number_type_fields(self):
        result={}
        for element in self.structure:
            if "type" in element and element["type"] == "number":
                if element["name"] in self.expiryConditions['fields']:
                    element_name = self.expiryConditions['fields'][element["name"]]
                    result[element["name"]] = element_name
                else:
                    result[element["name"]]={"type":"number", "condition": None}
        return result

    def get_multichoice_fields(self):
        result=[]
        for element in self.structure:
            if "type" in element:
                if  element["type"] == "checkbox-group" or \
                    element["type"] == "radio-group" or \
                    element["type"] == "select":
                    result.append(element)
        return result

    def get_field_label(self, fieldName):
        for element in self.structure:
            if 'name' in element and element['name']==fieldName:
                return element['label']
        return None

    def save_expiry_date(self, expireDate):
        self.expiryConditions['expireDate']=expireDate
        self.expired=self.has_expired()
        flag_modified(self, "expiryConditions")
        self.save()

    def save_expiry_total_answers(self, total_answers):
        try:
            total_answers = int(total_answers)
        except:
            total_answers = 0
        total_answers = 0 if total_answers < 0 else total_answers
        self.expiryConditions['totalAnswers']=total_answers
        self.expired = self.has_expired()
        flag_modified(self, "expiryConditions")
        self.save()
        return self.expiryConditions['totalAnswers']

    def save_expiry_field_condition(self, field_name, condition):
        available_fields=self.get_available_number_type_fields()
        if not field_name in available_fields:
            return False
        if not condition:
            if field_name in self.expiryConditions['fields']:
                del self.expiryConditions['fields'][field_name]
                self.expired=self.has_expired()
                flag_modified(self, "expiryConditions")
                self.save()
            return False
        field_type = available_fields[field_name]['type']
        if field_type == "number":
            try:
                condition_dict = {"type": field_type, "condition": int(condition)}
                self.expiryConditions['fields'][field_name] = condition_dict
            except:
                condition = False
                if field_name in self.expiryConditions['fields']:
                    del self.expiryConditions['fields'][field_name]
            self.expired=self.has_expired()
            flag_modified(self, "expiryConditions")
            self.save()
            return condition
        return False

    def update_expiryConditions(self):
        saved_expiry_fields = [field for field in self.expiryConditions['fields']]
        available_expiry_fields = []
        #available_expiry_fields=[element["name"] for element in self.structure if "name" in element]
        for element in self.structure:
            if "name" in element:
                available_expiry_fields.append(element["name"])
        for field in saved_expiry_fields:
            if not field in available_expiry_fields:
                del self.expiryConditions['fields'][field]

    def get_expiry_numberfield_positions_in_field_index(self):
        field_positions=[]
        for fieldName, condition in self.expiryConditions['fields'].items():
            if condition['type'] == 'number':
                for position, field in enumerate(self.fieldIndex):
                    if field['name'] == fieldName:
                        field_positions.append(position)
                        break
        return field_positions

    def delete(self):
        self.delete_all_answers()
        super().delete()

    def get_attachment_dir(self):
        return os.path.join(current_app.config['UPLOADS_DIR'],
                            current_app.config['ATTACHMENT_DIR'],
                            str(self.id))

    def delete_all_answers(self):
        self.answers.delete()
        attachment_dir = self.get_attachment_dir()
        if os.path.isdir(attachment_dir):
            shutil.rmtree(attachment_dir, ignore_errors=True)
        else:
            current_app.logger.debug(f"Local attachment dir not found: {attachment_dir}")
        if current_app.config['ENABLE_REMOTE_STORAGE'] == True:
            RemoteStorage().remove_directory(f"attachments/{self.id}")

    def is_author(self, user):
        return True if self.author_id == user.id else False

    def is_editor(self, user):
        return True if FormUser.find(user_id=user.id,
                                     form_id=self.id,
                                     is_editor=True) else False

    def get_editors(self, **kwargs):
        kwargs = {**{'is_editor': True}, **kwargs}
        return self.get_users(**kwargs)

    def get_readers(self, **kwargs):
        kwargs = {**{'is_editor': False}, **kwargs}
        return self.get_users(**kwargs)

    def get_users(self, **kwargs):
        from liberaforms.models.user import User
        kwargs = {**{'form_id': self.id}, **kwargs}
        return User.query.join(FormUser, User.id == FormUser.user_id) \
                         .filter_by(**kwargs)

    def can_expire(self):
        if self.expiryConditions["totalAnswers"]:
            return True
        if self.expiryConditions["expireDate"]:
            return True
        if self.expiryConditions["fields"]:
            return True
        return False

    def has_expired(self):
        if not self.can_expire():
            return False
        if self.expiryConditions["totalAnswers"] and \
            self.answers.count() >= self.expiryConditions["totalAnswers"]:
            return True
        if self.expiryConditions["expireDate"] and not \
            validators.is_future_date(self.expiryConditions["expireDate"]):
            return True
        for fieldName, value in self.expiryConditions['fields'].items():
            if value['type'] == 'number':
                total=self.tally_number_field(fieldName)
                if total >= int(value['condition']):
                    return True
        return False

    def tally_number_field(self, fieldName):
        total=0
        for answer in self.get_answers():
            try:
                total = total + int(answer.data[fieldName])
            except:
                continue
        return total

    def is_public(self):
        if not self.is_enabled() or self.expired:
            return False
        else:
            return True

    def are_answers_shared(self):
        return True if FormUser.find_all(form_id=self.id,
                                         is_editor=False).count() > 0 else False

    def get_shared_answers_url(self, part="results"):
        return f"{self.url}/{part}/{self.id}"

    """
    Used when editing a form.
    We don't want the Editor to change the option values if an
    answer.data[key] with a value is already present in the database
    """
    def get_multichoice_options_with_saved_data(self):
        result = {}
        if not self.answers:
            return result
        multiChoiceFields = {}  # {field.name: [option.value, option.value]}
        for field in self.get_multichoice_fields():
            multiChoiceFields[field['name']] = []
            for value in field['values']:
                multiChoiceFields[field['name']].append(value['value'])
        for answer in self.answers:
            removeFieldsFromSearch=[]
            for field in multiChoiceFields:
                if field in answer.data.keys():
                    for savedValue in answer.data[field].split(', '):
                        if savedValue in multiChoiceFields[field]:
                            if not field in result:
                                    result[field]=[]
                            result[field].append(savedValue)
                            multiChoiceFields[field].remove(savedValue)
                            if multiChoiceFields[field] == []:
                                # all option.values are present in database
                                removeFieldsFromSearch.append(field)
            for field_to_remove in removeFieldsFromSearch:
                del(multiChoiceFields[field_to_remove])
                if multiChoiceFields == {}: # no more fields to check
                    return result
        return result

    def get_answers_for_json(self):
        result=[]
        answers = self.get_answers_for_display(oldest_first=True)
        for saved_answer in answers:
            answer={}
            for field in self.get_field_index_for_data_display():
                #value=saved_answer[field['name']] if field['name'] in saved_answer else ""
                if field['name'] in saved_answer:
                    value = saved_answer[field['name']]
                else:
                    value = ""
                answer[field['label']]=value
            result.append(answer)
        return result

    def get_chart_data(self):
        chartable_time_fields=[]
        total={'answers':0}
        time_data={'answers':[]}
        for field in self.get_available_number_type_fields():
            label=self.get_field_label(field)
            total[label]=0
            time_data[label]=[]
            chartable_time_fields.append({'name':field, 'label':label})

        multichoice_fields=self.get_multichoice_fields()
        multi_choice_for_chart=[]
        for field in multichoice_fields:
            field_for_chart={   "name":field['name'], "title":field['label'],
                                "axis_1":[], "axis_2":[]}
            multi_choice_for_chart.append(field_for_chart)

            for value in field['values']:
                field_for_chart['axis_1'].append(value['label'])
                field_for_chart['axis_2'].append(0) #start counting at zero
        for answer in self.get_answers_for_display(oldest_first=True):
            total['answers']+=1
            time_data['answers'].append({   'x': answer['created'],
                                            'y': total['answers']})
            for field in chartable_time_fields:
                try:
                    total[field['label']]+=int(answer[field['name']])
                    time_data[field['label']].append({'x': answer['created'],
                                                      'y': total[field['label']]
                                                    })
                except:
                    continue
            for field in multichoice_fields:
                if not (field['name'] in answer and answer[field['name']]):
                    continue
                field_for_chart=[item for item in multi_choice_for_chart if item["name"]==field['name']][0]
                answer_values=answer[field['name']].split(', ')
                for idx, field_value in enumerate(field['values']):
                    if field_value['value'] in answer_values:
                        field_for_chart['axis_2'][idx]+=1
        return {'multi_choice':multi_choice_for_chart,
                'time_chart':time_data}

    def toggle_enabled(self):
        if self.expired or self.adminPreferences['public']==False:
            return False
        else:
            self.enabled = False if self.enabled else True
            self.save()
            return self.enabled

    def toggle_admin_form_public(self):
        public = self.adminPreferences['public']
        self.adminPreferences['public'] = False if public else True
        self.save()
        return self.adminPreferences['public']

    def toggle_shared_answers(self):
        enabled = self.sharedAnswers['enabled']
        self.sharedAnswers['enabled'] = False if enabled else True
        self.save()
        return self.sharedAnswers['enabled']

    def toggle_restricted_access(self):
        self.restrictedAccess = False if self.restrictedAccess else True
        self.save()
        return self.restrictedAccess

    def toggle_send_confirmation(self):
        self.sendConfirmation = False if self.sendConfirmation else True
        self.save()
        return self.sendConfirmation

    def add_log(self, message):
        log = FormLog(  user_id=g.current_user.id,
                        form_id=self.id,
                        message=message)
        log.save()

    def write_csv(self, with_deleted_columns=False):
        fieldnames=[]
        fieldheaders={}
        for field in self.get_field_index_for_data_display(with_deleted_columns):
            fieldnames.append(field['name'])
            fieldheaders[field['name']]=field['label']
        csv_name = os.path.join(os.environ['TMP_DIR'], f"{self.slug}.csv")
        with open(csv_name, mode='wb') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=fieldnames,
                                    extrasaction='ignore')
            writer.writerow(fieldheaders)
            answers = self.get_answers_for_display(oldest_first=True)
            for answer in answers:
                for field_name in answer.keys():
                    if field_name.startswith('file-'):
                        # extract attachment url
                        url = re.search(r'https?:[\'"]?([^\'" >]+)',
                                        answer[field_name])
                        if url:
                            answer[field_name] = url.group(0)
                writer.writerow(answer)
        return csv_name

    @staticmethod
    def default_introduction_text():
        # i18n: Example title in template for new form
        title=_("Form title")
        # i18n: Example subtitle in template for new form
        context=_("Context")
        # i18n: Example content in template for new form. '\n' is used for linebreak.
        content=_(" * Describe your form.\n * Add relevant content, links, images, etc.")
        return "## {}\n\n### {}\n\n{}".format(title, context, content)
