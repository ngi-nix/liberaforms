from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
mongo = PyMongo(app)

from formbuilder import views

if __name__ == '__main__':
        app.run()
