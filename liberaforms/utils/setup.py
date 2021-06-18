"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""


import os, logging, shutil

def ensure_uploads_dir_tree(app):

    uploads_dir = app.config['UPLOADS_DIR']
    media_dir = os.path.join(uploads_dir, app.config['MEDIA_DIR'])
    attachment_dir = os.path.join(uploads_dir, app.config['ATTACHMENT_DIR'])
    if not os.path.isdir(media_dir):
        os.makedirs(media_dir)
        shutil.copytree(os.path.join(app.config['ROOT_DIR'], 'assets', 'brand'),
                        os.path.join(uploads_dir, app.config['BRAND_DIR']))
    if not os.path.isdir(attachment_dir):
        os.makedirs(attachment_dir)
    logging.debug("Uploads dir tree in place")
