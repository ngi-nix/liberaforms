"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms.utils import sanitizers
from liberaforms.utils import utils
from flask_babel import gettext as _
from copy import copy
#from pprint import pprint as pp


"""
variable obj is a Form or User or Site object.
"""

class ConsentText():
    def __init__(self, *args, **kwargs):        
        pass
    
    @staticmethod
    def _get_consent_by_id(id, obj):           
        consent = [item for item in obj.consentTexts if item["id"]==id]
        #pp({"obj": obj.__class__.__name__, "consents on getByID" :obj.consentTexts})
        return consent[0] if consent else None

    @staticmethod
    def _save(consent, obj):
        obj.consentTexts = [consent if item["id"]==consent["id"] else item for item in obj.consentTexts]
        obj.save()

    @classmethod
    def get_consent_for_display(cls, id, obj):
        consent = copy(cls._get_consent_by_id(id, obj))
        if not consent:
            return None

        if obj.__class__.__name__=="Form":
            obj = obj.get_author()
            user_consent = cls._get_consent_by_id(id, obj)
            if user_consent:
                consent['markdown'] = consent['markdown'] if consent['markdown'] else user_consent['markdown']
                consent['html'] = consent['html'] if consent['html'] else user_consent['html']
                consent['label'] = consent['label'] if consent['label'] else user_consent['label']
        if obj.__class__.__name__=="User":
            # we will add code here when user defined ConsentTexts are enabled (future)
            obj=obj.site
        
        if obj.__class__.__name__=="Site":
            site_consent=obj.get_consent_for_display(consent['id'], enabled_only=True)
            if site_consent:
                if site_consent['markdown'] and not consent['markdown']:
                    consent['markdown'] = site_consent['markdown']
                    consent['html'] = site_consent['html']                
                if site_consent['label'] and not consent['label']:
                    consent['label'] = site_consent['label']
        consent['label'] = consent['label'] if consent['label'] else "{}".format(_("I agree"))
        return consent

    """
    Saves Form and User consentTexts
    """
    @classmethod
    def save(cls, id, obj, data):
        if obj.__class__.__name__ == "Site":
            return None
        consent = cls._get_consent_by_id(id, obj)
        if not consent:
            return None
        consent['markdown'] = sanitizers.escape_markdown(data['markdown'].strip())
        consent['html'] = sanitizers.markdown2HTML(consent['markdown'])
        consent['label'] = sanitizers.strip_html_tags(data['label']).strip()
        consent['required'] = utils.str2bool(data['required'])
        
        default_consent=None        
        if obj.__class__.__name__ == "Form":
            default_consent = cls._get_consent_by_id(id, obj.get_author())
        if not default_consent:
            site_obj = obj if obj.__class__.__name__ == "Site" else obj.site
            default_consent = site_obj.get_consent_for_display(consent['id'], enabled_only=True)
        if default_consent:
            if consent['markdown'] == default_consent['markdown']:
                consent['markdown'] = ""
                consent['html'] = ""
            if consent['label'] == default_consent['label']:
                consent['label'] = ""
        cls._save(consent, obj)
        return cls.get_consent_for_display(consent['id'], obj)

    @classmethod
    def toggle_enabled(cls, id, obj):
        consent = cls._get_consent_by_id(id, obj)
        if consent:
            consent['enabled'] = False if consent['enabled'] else True
            cls._save(consent, obj)
            return consent['enabled']
        return False

    @staticmethod
    def get_empty_consent(id=None, name="", enabled=False, required=True):
        return {"id": id,
                "name": name,
                "markdown": "",
                "html": "",
                "label": "",
                "required": required,
                "enabled": enabled}
    
    @staticmethod
    def default_terms(id=None, enabled=False):
        text=_("Please accept our terms and conditions.")
        return {"id":id,
                "name":"terms",
                "markdown":text,
                "html":"<p>"+text+"</p>",
                "label":"",
                "required":True,
                "enabled": enabled}

    @staticmethod
    def default_DPL(id=None, enabled=False):
        title=_("DPL")
        text=_("We take your data protection seriously. Please contact us for any inquiries.")
        markdown="###### {}\n\n{}".format(title, text)
        html = "<h6>{}</h6><p>{}</p>".format(title, text)
        return {"id":id,
                "name":"DPL",
                "markdown":markdown,
                "html": html,
                "label":"",
                "required":True,
                "enabled": enabled}
