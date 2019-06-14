from formbuilder import mongo

def getForm(slug):
    queriedForm = mongo.db.forms.find_one({"slug": slug})
    if queriedForm:
        return dict(queriedForm)
    return None


def updateForm(slug, data):
    mongo.db.forms.update_one({'slug':slug}, {"$set": data})


def insertForm(formData):
    mongo.db.forms.insert_one(formData)


def findForms():
    return mongo.db.forms.find()
