"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, shutil
from io import BytesIO
import logging
from flask import current_app
from liberaforms.utils.storage.remote import RemoteStorage


class Storage:
    def storage_directory_path(self, sub_dir):
        return os.path.join(current_app.config['UPLOAD_DIR'], sub_dir)

    def save_file(self, file, sub_dir, storage_name):
        tmp_dir = current_app.config['TMP_DIR']
        tmp_file_path = f"{tmp_dir}/{storage_name}"
        file.save(tmp_file_path)
        if current_app.config['ENABLE_REMOTE_STORAGE']:
            saved = RemoteStorage().add_object(tmp_file_path,
                                               sub_dir,
                                               storage_name)
            if saved == True:
                self.local_filesystem = False
                os.remove(tmp_file_path)
                return True
        local_storage_dir = self.storage_directory_path(sub_dir)
        if not os.path.exists(local_storage_dir):
            os.makedirs(local_storage_dir)
        file_path = os.path.join(local_storage_dir, storage_name)
        shutil.copyfile(tmp_file_path, file_path)
        return True

    def get_file(self, sub_dir, storage_name):
        if self.local_filesystem:
            local_storage_dir = self.storage_directory_path(sub_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    return BytesIO(file.read())
            return False
        else:
            tmp_file_path = RemoteStorage().get_object(sub_dir, storage_name)
            if os.path.exists(tmp_file_path):
                with open(tmp_file_path, 'rb') as file:
                    bytes = BytesIO(file.read())
                os.remove(tmp_file_path)
                return bytes
            return False

    def delete_file(self, sub_dir, storage_name):
        if self.local_filesystem:
            local_storage_dir = self.storage_directory_path(sub_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        else:
            removed = RemoteStorage().remove_object(sub_dir, storage_name)
            return removed
