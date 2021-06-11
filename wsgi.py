"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, logging
from flask_migrate import Migrate
from liberaforms import create_app, db

app = create_app()

migrate = Migrate(app, db)

if app.config['ENABLE_REMOTE_STORAGE']:
    from liberaforms.utils.storage.remote import RemoteStorage
    with app.app_context():
        logging.debug("Checking for remote buckets")
        if not RemoteStorage().ensure_buckets_exist():
            logging.error("Buckets are not configured correctly !!")



@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)
