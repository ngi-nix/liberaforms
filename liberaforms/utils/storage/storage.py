"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import logging
from flask import current_app
from liberaforms.utils.storage.remote import RemoteStorage


class Storage:
    def storage_directory_path(self, sub_dir):
        return os.path.join(current_app.config['UPLOAD_DIR'], sub_dir)

    def save_file(self, file, sub_dir, storage_name):
        storage_dir = self.storage_directory_path(sub_dir)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        file_path = os.path.join(storage_dir, storage_name)
        file.save(file_path)
        uploaded = False
        if current_app.config['ENABLE_REMOTE_STORAGE']:
            uploaded = RemoteStorage().add_object(file_path, sub_dir, storage_name)
        if uploaded:
            os.remove(file_path)
        return True

    def delete_file(self, sub_dir, storage_name):
        removed = False
        if current_app.config['ENABLE_REMOTE_STORAGE']:
            removed = RemoteStorage().remove_object(sub_dir, storage_name)
        if not removed:
            storage_dir = self.storage_directory_path(sub_dir)
            file_path = os.path.join(storage_dir, storage_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                removed = True
        return removed
