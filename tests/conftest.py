"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask_migrate import Migrate, upgrade
from liberaforms import create_app
from liberaforms import db as _db


"""
Returns app
"""
@pytest.fixture(scope='session')
def app():
    flask_app = create_app()
    yield flask_app

"""
Upgrades the database schema with alembic
"""
@pytest.fixture(scope='session')
def db(app):
    migrate = Migrate(app, _db, directory='../migrations')
    with app.app_context():
        upgrade()
    yield _db

@pytest.fixture(scope='session')
def session(db):
    connection = db.engine.connect()
    #transaction = connection.begin()

    options = dict(bind=connection)
    session = db.create_scoped_session(options=options)
    db.session = session
    yield session


@pytest.fixture(scope='session')
def client(app):
    with app.test_client() as client:
        yield client

"""
@pytest.fixture(scope='function')
def session(request, db):
    session = db['session_factory']()
    yield session
    print('\n----- CREATE DB SESSION\n')

    session.rollback()
    session.close()
    print('\n----- ROLLBACK DB SESSION\n')
"""
