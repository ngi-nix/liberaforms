"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import app

#from pprint import pprint as pp


def migrateMongoSchema(schemaVersion):
    from liberaforms.models.site import Site, Installation
    from liberaforms.models.form import Form, FormResponse
    from liberaforms.models.user import User

    if schemaVersion == 13:
        query = Form.objects()
        query.update(set__introductionText={"markdown":"", "html":""})
        schemaVersion = 14

    if schemaVersion == 14:
        print("Upgrading to version 15")
        try:
            collection = Form._get_collection()
            for f in collection.find():
                consent=f["requireDataConsent"]
                collection.update_one(  {"_id": f["_id"]},
                                        {"$set": { "requireDataConsent": {  "markdown":"",
                                                                            "html":"",
                                                                            "required": consent}}})
                collection.update_one(  {"_id": f["_id"]},
                                        {"$rename": {"requireDataConsent": "dataConsent"} })
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 15

    if schemaVersion == 15:
        print("Upgrading to version 16")
        import uuid
        try:
            collection = Form._get_collection()
            for form in collection.find():
                form["fieldIndex"].insert(0, {'label':"Marked", 'name':'marked'})
                collection.update_one(  {"_id": form["_id"]},
                                        {"$set": {"fieldIndex": form["fieldIndex"]} })
                # We found an old form (created from a template) with this key missing. (gulps).
                if not 'entries' in form:
                    collection.update_one(  {"_id": form["_id"]},
                                            {"$set": {"entries": []} })
                    print("Added missing entries[] to %s %s" % (form['hostname'], form['slug']))
                    continue
                for entry in form["entries"]:
                    if not 'marked' in entry:
                        entry['marked']=False
                    if not 'id' in entry:
                        _id=uuid.uuid4()
                        entry['id']=str(_id)
                collection.update_one(  {"_id": form["_id"]},
                                        {"$set": {"entries": form["entries"]} })                
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 16

    if schemaVersion == 16:
        print("Upgrading to version 17")
        try:
            query = Form.objects()
            query.update(set__sendConfirmation=False)
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 17

    if schemaVersion == 17:
        print("Upgrading to version 18")
        try:
            query = Site.objects()
            query.update(   set__menuColor="#802C7D",
                            set__defaultLanguage=app.config['DEFAULT_LANGUAGE'])
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 18

    if schemaVersion == 18:
        print("Upgrading to version 19")
        try:
            collection = User._get_collection()
            for user in collection.find():
                language=user["language"]
                collection.update_one(  {"_id": user["_id"]},
                                        {"$set": { "preferences": { "language": language,
                                                                    "newEntryNotification": False
                                                                    }}})
                collection.update_one(  {"_id": user["_id"]},
                                        {"$unset": {"language": 1} })
            query = Form.objects()
            query.update(set__expiredText={"markdown":"", "html":""})
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 19

    if schemaVersion == 19:
        print("Upgrading to version 20")
        try:
            collection = Site._get_collection()
            collection.update_many({}, {"$set": { "termsAndConditions": {
                                                    "markdown":"", "html":"", "enabled":False}
                                                }})
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 20

    if schemaVersion == 20:
        print("Upgrading to version 21")
        import json
        try:
            collection = Form._get_collection()
            for form in collection.find():
                structure=json.loads(form["structure"])
                collection.update_one(  {"_id": form["_id"]},
                                        {"$set": { "structure": structure}})
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 21

    if schemaVersion == 21:
        print("Upgrading to version 22")
        from liberaforms.utils.consent_texts import ConsentText
        import uuid
        try:
            user_collection = User._get_collection()
            site_collection = Site._get_collection()
            form_collection = Form._get_collection()
            user_collection.update_many({}, {"$set": {"consentTexts": []}})
            for site in site_collection.find():
                terms_id = uuid.uuid4().hex
                new_user_consentment_texts = []
                if site["termsAndConditions"]['html']:
                    terms_text = {  **site["termsAndConditions"],
                                    "id": terms_id,
                                    "name":"terms",
                                    "label":"",
                                    "required":True}
                    new_user_consentment_texts.append(terms_id)
                else:
                    terms_text = ConsentText.get_empty_consent(id=terms_id, name="terms")
                DPL_id = uuid.uuid4().hex
                for form in form_collection.find({"hostname": site["hostname"]}):
                    DPL_text = {"id": DPL_id,
                                "name": "DPL",
                                "label": "",
                                "enabled": form["dataConsent"]["required"],
                                "required": True,
                                "markdown": form["dataConsent"]["markdown"],
                                "html": form["dataConsent"]["html"]
                            }                       
                    form_collection.update_one( {"_id": form["_id"]},
                                                {"$set": { "consentTexts": [DPL_text]}})
                    form_collection.update_one( {"_id": form["_id"]},
                                                {"$unset": {"dataConsent": 1 }})
                if site["personalDataConsent"]['html']:
                    DPL_text = {**site["personalDataConsent"],
                                "id": DPL_id,
                                "name":"DPL",
                                "label":"",
                                "required":True
                                }
                else:
                    DPL_text = ConsentText.get_empty_consent(id=DPL_id,name="DPL")
                site_collection.update_one(  {"_id": site["_id"]},
                                        {"$set": {  "consentTexts": [terms_text, DPL_text],
                                                    "newUserConsentment": new_user_consentment_texts}})
                site_collection.update_one(  {"_id": site["_id"]},
                                        {"$unset": {"personalDataConsent": 1,
                                                    "termsAndConditions": 1 } })
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 22

    # https://api.mongodb.com/python/current/tutorial.html#range-queries
    if schemaVersion == 22:
        print("Upgrading to version 23")
        try:
            form_collection = Form._get_collection()
            for form in form_collection.find():
                if hasattr(form, 'entries'):
                    for entry in form['entries']:
                        created=entry['created']
                        marked=entry['marked']
                        del entry['id']
                        del entry['created']
                        del entry['marked']
                        new_data = {
                                "created": created,
                                "hostname": form['hostname'],
                                "author_id": str(form['author']),
                                "form_id": str(form["_id"]),
                                "marked": marked,
                                "data": entry}
                        response = FormResponse(**new_data)
                        response.save()
            form_collection.update_many( {}, {"$unset": {"entries": 1} })
    
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 23

    if schemaVersion == 23:
        print("Upgrading to version 24")
        try:
            collection = Form._get_collection()
            collection.update_many({}, {"$set": {"expiryConditions.totalEntries": 0} })
            created_date = Installation.get().created
            collection = Site._get_collection()
            collection.update_many({}, {"$set": {"created": created_date} })
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 24

    return schemaVersion
