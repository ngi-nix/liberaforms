"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask_migrate import Migrate, upgrade
from liberaforms import create_app, db


@pytest.fixture(scope='session')
def app():
    flask_app = create_app()
    migrate = Migrate(flask_app, db, directory='../migrations')
    with flask_app.app_context():
            upgrade()
    yield flask_app


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
