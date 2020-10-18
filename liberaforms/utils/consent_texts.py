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

from liberaforms.utils.utils import *
from flask_babel import gettext as _
from copy import copy
#from pprint import pprint as pp


class ConsentText():
    
    def __init__(self, *args, **kwargs):        
        pass
    
    @staticmethod
    def getConsentByID(id, scope):           
        consent = [item for item in scope.consentTexts if item["id"]==id]
        #pp({"scope": scope.__class__.__name__, "consents on getByID" :scope.consentTexts})
        return consent[0] if consent else None

    @classmethod
    def _save(cls, consent, scope):
        scope.consentTexts = [consent if item["id"]==consent["id"] else item for item in scope.consentTexts]
        scope.save()

    @classmethod
    def getConsentForDisplay(cls, id, scope):
        consent = copy(cls.getConsentByID(id, scope))
        if not consent:
            return None

        if scope.__class__.__name__=="Form":
            user_consent=cls.getConsentByID(id, scope.getAuthor())
            if user_consent:
                consent['markdown'] = consent['markdown'] if consent['markdown'] else user_consent['markdown']
                consent['html'] = consent['html'] if consent['html'] else user_consent['html']
                consent['label'] = consent['label'] if consent['label'] else user_consent['label']
            scope = scope.getAuthor()
        
        if scope.__class__.__name__=="User":
            scope=scope.site
        
        if scope.__class__.__name__=="Site":
            site_consent=scope.getConsentForDisplay(consent['id'], enabled_only=True)
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
    def save(cls, id, scope, data):
        if scope.__class__.__name__ == "Site":
            return None
        consent = cls.getConsentByID(id, scope)
        if not consent:
            return None
        consent['markdown'] = escapeMarkdown(data['markdown'].strip())
        consent['html'] = markdown2HTML(consent['markdown'])
        consent['label'] = stripHTMLTags(data['label']).strip()
        consent['required'] = str2bool(data['required'])
        
        default_consent=None        
        if scope.__class__.__name__ == "Form":
            default_consent = cls.getConsentByID(id, scope.getAuthor())
        if not default_consent:
            site_scope = scope if scope.__class__.__name__ == "Site" else scope.site
            default_consent = site_scope.getConsentForDisplay(consent['id'], enabled_only=True)
        if default_consent:
            if consent['markdown'] == default_consent['markdown']:
                consent['markdown'] = ""
                consent['html'] = ""
            if consent['label'] == default_consent['label']:
                consent['label'] = ""
        cls._save(consent, scope)
        return cls.getConsentForDisplay(consent['id'], scope)

    @classmethod
    def toggleEnabled(cls, id, scope):
        consent = cls.getConsentByID(id, scope)
        if consent:
            consent['enabled'] = False if consent['enabled'] else True
            cls._save(consent, scope)
            return consent['enabled']
        return False

    @staticmethod
    def getEmptyConsent(id=None, name="", enabled=False, required=True):
        return {"id": id,
                "name": name,
                "markdown": "",
                "html": "",
                "label": "",
                "required": required,
                "enabled": enabled}
    
    @staticmethod
    def defaultTerms(id=None, enabled=False):
        text=_("Please accept our terms and conditions.")
        return {"id":id, "name":"terms", "markdown":text, "html":"<p>"+text+"</p>", "label":"", "required":True, "enabled": enabled}

    @staticmethod
    def defaultDPL(id=None, enabled=False):
        title=_("DPL")
        text=_("We take your data protection seriously. Please contact us for any inquiries.")
        markdown="###### {}\n\n{}".format(title, text)
        html = "<h6>{}</h6><p>{}</p>".format(title, text)
        return {"id":id, "name":"DPL", "markdown":markdown, "html": html, "label":"", "required":True, "enabled": enabled}
