"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import ast

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['DB_USER'] = os.environ['TEST_DB_USER']
os.environ['DB_PASSWORD'] = os.environ['TEST_DB_PASSWORD']
os.environ['DB_HOST'] = os.environ['TEST_DB_HOST']
os.environ['DB_NAME'] = os.environ['TEST_DB_NAME']

import pytest
from flask_migrate import Migrate, upgrade, stamp
from liberaforms import create_app
from liberaforms import db as _db

"""
Returns app
"""
@pytest.fixture(scope='session')
def app():
    flask_app = create_app()
    # change the uploads dir to tests/uploads/
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    flask_app.config['UPLOADS_DIR'] = os.path.abspath(os.path.join(tests_dir, 'uploads'))
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

@pytest.fixture(scope='session')
def admin_client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='session')
def anon_client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='class')
def users():
    root_user_email = ast.literal_eval(os.environ['ROOT_USERS'])[0]
    root_user_username = root_user_email.split('@')[0]
    return {
        #"user": None,
        "editor": {
            "username": os.environ['USER1_USERNAME'],
            "email": os.environ['USER1_EMAIL'],
            "password": os.environ['USER1_PASSWORD']
        },
        "admin": {
            "username": root_user_username,
            "email": root_user_email,
            "password": "this is a valid password"
        },
        "dummy_1": {
            "username": "dave",
            "email": "dave@example.com",
            "password": "another valid password"
        }
    }
