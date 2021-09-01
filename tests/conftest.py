"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, ast, time
import shutil

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['DB_USER'] = os.environ['TEST_DB_USER']
os.environ['DB_PASSWORD'] = os.environ['TEST_DB_PASSWORD']
os.environ['DB_HOST'] = os.environ['TEST_DB_HOST']
os.environ['DB_NAME'] = os.environ['TEST_DB_NAME']

import pytest
from flask_migrate import Migrate, upgrade, stamp
from liberaforms import create_app
from liberaforms import db as _db

media_dir = os.path.join(os.getcwd(), "uploads/media/hosts/localhost")
attach_dir = os.path.join(os.getcwd(), "uploads/attachments/hosts/localhost")
shutil.rmtree(media_dir, ignore_errors=True)
shutil.rmtree(attach_dir, ignore_errors=True)

"""
Returns app
"""
@pytest.fixture(scope='session')
def app():
    flask_app = create_app()
    yield flask_app

"""
Upgrades database schema with alembic
Yields db
Drops tables
"""
@pytest.fixture(scope='session')
def db(app):
    migrate = Migrate(app, _db, directory='../migrations')
    with app.app_context():
        _db.drop_all()
        #pytest.exit("out")
        stamp(revision='base')
        upgrade()
        yield _db
        #_db.drop_all()
        #stamp(revision='base')

@pytest.fixture(scope='session')
def session(db):
    connection = db.engine.connect()
    #transaction = connection.begin()

    options = dict(bind=connection)
    session = db.create_scoped_session(options=options)
    db.session = session
    yield session

@pytest.fixture(autouse=True)
def run_around_tests():
    # Code that will run before your test
    # <- here
    yield
    # Code that will run after your test
    #time.sleep(0.2)



@pytest.fixture(scope='class')
def users():
    root_user_email = ast.literal_eval(os.environ['ROOT_USERS'])[0]
    return {
        "admin": {
            "username": "admin1",
            "email": root_user_email,
            "password": "this is a valid password"
        },
        "editor": {
            "username": os.environ['EDITOR_1_USERNAME'],
            "email": os.environ['EDITOR_1_EMAIL'],
            "password": os.environ['EDITOR_1_PASSWORD']
        },
        "dummy_1": {
            "username": "dummy1",
            "email": "dummy1@liberaforms.org",
            "password": "another valid password"
        },
        "dummy_2": {
            "username": "dummy2",
            "email": "dummy2@liberaforms.org",
            "password": "yet another valid password"
        },
    }
