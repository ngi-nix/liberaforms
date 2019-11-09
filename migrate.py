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
from GNGforms import persistence
import pprint

def migrateMongoSchema(schemaVersion):

    if schemaVersion < 2:
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
        schemaVersion=2

    if schemaVersion < 3:
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

    if schemaVersion < 4:
        # this originally didn't work
        # get rid of from ObjectIDs
        for form in mongo.db.forms.find():
            form['author']=str(form['author'])
            mongo.db.forms.save(form)
        # this originally didn't work
        for form in mongo.db.forms.find():
            newEditorsDict={}
            for editor in form['editors']:
                newEditorsDict[editor]={'notification': form['notification']}
            if not newEditorsDict:
                newEditorsDict[form['author']]={'notification': {'newEntry': False}}
            form['editors']=newEditorsDict
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$unset": {'notification' :1}, "$set": {"editors": form['editors']}})
        schemaVersion=4
    
    if schemaVersion < 5:
        for site in mongo.db.sites.find():
            site["siteName"]="GNGforms"
            mongo.db.sites.save(site)
        schemaVersion=5

    if schemaVersion < 6:
        # Add field conditions
        for form in mongo.db.forms.find():
            form["expiryConditions"]["fields"]={}
            conditions=form["expiryConditions"]
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$set": {"expiryConditions": conditions}})
        schemaVersion=6

    if schemaVersion < 7:
        # Add log array
        for form in mongo.db.forms.find():
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$set": {"log": []}})
        schemaVersion=7

    if schemaVersion < 8:
        # Add expired bool
        forms=[persistence.Form(_id=form['_id']) for form in mongo.db.forms.find()]
        for form in forms:
            for editor in form.data['editors']:
                form.data['editors'][editor]["notification"]["expiredForm"]=True
            form.update({   "expired": form.hasExpired(),
                            "editors": form.data['editors']
                        })
        schemaVersion=8

    if schemaVersion < 9:
        # Add site footnote. To be displayed at foot of forms.
        for site in mongo.db.sites.find():
            mongo.db.sites.update_one({"_id": site["_id"]}, {"$set": {"defaultFormFootNote": {
                                                                        'markdown': "",
                                                                        'html': "",
                                                                        'enabled': False }} })
        for form in mongo.db.forms.find():
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$set": {"showFootNote": False }})
                                                        
        schemaVersion=9

    if schemaVersion < 10:
        # Changed site footnote to personalDataConsent.
        for site in mongo.db.sites.find():
            consent=site["defaultFormFootNote"]
            mongo.db.sites.update_one({"_id": site["_id"]}, {"$unset": {'defaultFormFootNote' :1}, "$set": {"personalDataConsent": consent} })
              
        for form in mongo.db.forms.find():
            boolean=form["showFootNote"]
            mongo.db.forms.update_one({"_id": form["_id"]}, {"$unset": {'showFootNote' :1}, "$set": {"requireDataConsent": boolean }})
            
        schemaVersion=10


    # this can't be a good migration setup :(
    return schemaVersion
