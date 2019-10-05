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

from GNGforms import mongo
import pprint

def migrateMongoSchema(schemaVersionBeforeUpdate):
    schemaVersion=None
    
    # changes in schema version 2
    # replace "expireDate" for "expiryConditions"
    for form in mongo.db.forms.find():
        if 'expireDate' in form:
            expireDate=form['expireDate']
            form["expiryConditions"] = {"expireDate": expireDate}
            mongo.db.forms.save(form)
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$unset": {'expireDate' :1}})
        else:
            break
    
    # get rid of from ObjectIDs
    for form in mongo.db.forms.find():
        if not isinstance(form['author'], str):
            form['author']=str(form['author'])
            mongo.db.forms.save(form)
        else:
            break

    """
    # add the form author to the editors list
    for form in mongo.db.forms.find():
        if form['editors'] == []:
            form['editors'] = {}
            form['editors'][form['author']]={'notification': form['notification']}
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$unset": {'notification' :1}, "$set": {"editors": form['editors']}})
        else:
            break
    """
    schemaVersion=2
    
    # changes in schema version 2
    # change the editor's list to a dict and include notification preferences
    for form in mongo.db.forms.find():
        if isinstance(form['editors'], list):
            newEditorsDict={}
            for editor in form['editors']:
                newEditorsDict[editor]={'notification': form['notification']}
            form['editors']=newEditorsDict
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$unset": {'notification' :1}, "$set": {"editors": form['editors']}})
        else:
            break
    schemaVersion=3
    
    return schemaVersion
