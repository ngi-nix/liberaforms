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

from gngforms import models
#from pprint import pprint as pp


def migrateMongoSchema(schemaVersion):

    if schemaVersion == 13:
        query = models.Form.objects()
        query.update(set__introductionText={"markdown":"", "html":""})
        schemaVersion = 14

    if schemaVersion == 14:
        print("Upgrading to version 15")
        try:
            # Using raw mongo instead of the engine because "requireDataConsent"
            # was removed from models.Forms in this version of gngforms.
            collection = models.Form._get_collection()
            for f in collection.find():
                consent=f["requireDataConsent"]
                collection.update_one(  {"_id": f["_id"]},
                                        {"$set": { "requireDataConsent": {  "markdown":"",
                                                                            "html":"",
                                                                            "required": consent}}})
                collection.update_one(  {"_id": f["_id"]},
                                        {"$rename": {"requireDataConsent": "dataConsent"} })
        except:
            print("Failed")
            return schemaVersion
        print("OK")
        schemaVersion = 15

    if schemaVersion == 15:
        print("Upgrading to version 16")
        import uuid
        try:
            for form in models.Form.objects():
                for entry in form.entries:
                    if not 'marked' in entry:
                        entry['marked']=False
                    if not 'id' in entry:
                        _id=uuid.uuid4()
                        entry['id']=str(_id)
                form.fieldIndex.insert(0, {'label':"Marked", 'name':'marked'})
                form.save()
        except:
            print("Failed")
            return schemaVersion
        print("OK")
        schemaVersion = 16

    if schemaVersion == 16:
        print("Upgrading to version 17")
        try:
            for form in models.Form.objects():
                form.sendConfirmation=False
                form.save()
        except:
            print("Failed")
            return schemaVersion
        print("OK")
        schemaVersion = 17
        
    return schemaVersion
