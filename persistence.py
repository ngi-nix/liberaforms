from formbuilder import mongo


def getForm(slug):
    queriedForm = mongo.db.forms.find_one({"slug": slug})
    if queriedForm:
        return dict(queriedForm)
    return None


def insertForm(formData):
    mongo.db.forms.insert_one(formData)


def updateForm(slug, data):
    mongo.db.forms.update_one({'slug':slug}, {"$set": data})


def saveEntry(form, entry):
    mongo.db.forms.update({ "_id": form["_id"] }, {"$push": {"entries": entry }})


def findForms():
    return mongo.db.forms.find()

def getTotalEntries(form):
    return len(form["entries"])

def getLastEntryData(form):
    total_entries = len(form["entries"])
    if total_entries:
        last_entry = form["entries"][-1] 
        last_entry_date = last_entry["created"]
    else:
        last_entry_date = ""
