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

from gngforms import app, models
#from pprint import pprint as pp


def migrateMongoSchema(schemaVersion):

    if schemaVersion == 13:
        query = models.Form.objects()
        query.update(set__introductionText={"markdown":"", "html":""})
        schemaVersion = 14

    if schemaVersion == 14:
        print("Upgrading to version 15")
        try:
            collection = models.Form._get_collection()
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
            collection = models.Form._get_collection()
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
            query = models.Form.objects()
            query.update(set__sendConfirmation=False)
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 17

    if schemaVersion == 17:
        print("Upgrading to version 18")
        try:
            query = models.Site.objects()
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
            collection = models.User._get_collection()
            for user in collection.find():
                language=user["language"]
                collection.update_one(  {"_id": user["_id"]},
                                        {"$set": { "preferences": { "language": language,
                                                                    "newEntryNotification": False
                                                                    }}})
                collection.update_one(  {"_id": user["_id"]},
                                        {"$unset": {"language": 1} })
            query = models.Form.objects()
            query.update(set__expiredText={"markdown":"", "html":""})
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 19

    if schemaVersion == 19:
        print("Upgrading to version 20")
        try:
            query = models.Site.objects()
            query.update(set__termsAndConditions={"markdown":"", "html":"", "enabled":False})
        except Exception as e:
            print(e)
            return schemaVersion
        print("OK")
        schemaVersion = 20

    return schemaVersion
