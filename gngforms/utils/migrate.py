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

"""
Mirgations previous to schemaVersion 13 used the flask_pymongo library.
schemaVersion >= 13 uses flask_mongoengine.
"""

def migrateMongoSchema(schemaVersion):

    if schemaVersion == 13:
        query = models.Form.objects()
        query.update(set__introductionText={"markdown":"", "html":""})
        schemaVersion = 14

    if schemaVersion == 14:
        try:
            # usign raw mongo instead of the engine because "requireDataConsent"
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
            return schemaVersion
        schemaVersion = 15

    return schemaVersion
