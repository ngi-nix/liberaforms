from formbuilder import mongo
from .utils import getRandomString



class Form(object):
    form = None

    def __new__(cls, *args, **kwargs):
        instance = super(Form, cls).__new__(cls)
        if kwargs:
            form = mongo.db.forms.find_one(kwargs)
            if form:
                instance.form=dict(form)
            else:
                return None
        return instance

    
    def __init__(self, *args, **kwargs):
        pass

    @property
    def data(self):
        return self.form

    @property
    def author(self):
        return self.form['author']

    @property
    def slug(self):
        return self.form['slug']

    @property
    def structure(self):
        return self.form['structure']

    @structure.setter
    def structure(self, value):
        self.form['structure'] = value
    
    @property
    def fieldIndex(self):
        return self.form['fieldIndex']

    @fieldIndex.setter
    def fieldIndex(self, value):
        self.form['fieldIndex'] = value

    @property
    def entries(self):
        return self.form['entries']

    @property
    def created(self):
        return self.form['created']

    def findAll(*args, **kwargs):
        if kwargs:
            return mongo.db.forms.find(kwargs)
        return mongo.db.forms.find()


    def toggleEnabled(self):
        if self.form['enabled']:
            self.form['enabled']=False
        else:
            self.form['enabled']=True
        mongo.db.forms.save(self.form)
        return self.form['enabled']

    def insert(self, formData):
        mongo.db.forms.insert_one(formData)

    def update(self, data):
        mongo.db.forms.update_one({'slug':self.slug}, {"$set": data})
    
    def saveEntry(self, entry):
        mongo.db.forms.update({ "_id": self.form["_id"] }, {"$push": {"entries": entry }})

    @property
    def totalEntries(self):
        return len(self.entries)

    @property
    def enabled(self):
        return self.form['enabled']

    @property
    def lastEntryDate(self):
        if self.entries:
            last_entry = self.entries[-1] 
            last_entry_date = last_entry["created"]
        else:
            last_entry_date = ""
