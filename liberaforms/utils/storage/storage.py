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

    def save_to_disk(self, tmp_file_path, sub_dir, storage_name):
        local_storage_dir = self.storage_directory_path(sub_dir)
        try:
            if not os.path.exists(local_storage_dir):
                os.makedirs(local_storage_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            shutil.copyfile(tmp_file_path, file_path)
            return True
        except Exception as error:
            #logging.error(f"Failed to save file to local filesystem: {file_path}")
            logging.error(f"{error}: {file_path}")
            return False

    def save_file(self, file, sub_dir, storage_name):
        tmp_dir = current_app.config['TMP_DIR']
        tmp_file_path = f"{tmp_dir}/{storage_name}"
        try:
            file.save(tmp_file_path)
        except:
            logging.error(f"Upload failed. Cannot save to tmp_file. : {tmp_file_path}")
            return False
        if current_app.config['ENABLE_REMOTE_STORAGE']:
            try:
                saved = RemoteStorage().add_object(tmp_file_path,
                                                   sub_dir,
                                                   storage_name)
                if saved == True:
                    self.local_filesystem = False
                    os.remove(tmp_file_path)
                    return True
            except Exception as error:
                logging.error(error)
                logging.warning(f"Failed to save remote object. Saving to local filesystem.")
                saved = self.save_to_disk(tmp_file_path, sub_dir, storage_name)
                if saved == True:
                    return True
                else:
                    file_path = f"{sub_dir}/{storage_name}"
                    logging.error(f"Upload failed. Did not save file: {file_path}")
                    return False
        else:
            saved = self.save_to_disk(tmp_file_path, sub_dir, storage_name)
            if saved == True:
                return True
            else:
                file_path = f"{sub_dir}/{storage_name}"
                logging.error(f"Upload failed. Did not save file: {file_path}")
                return False

    def get_file(self, sub_dir, storage_name):
        if self.local_filesystem:
            local_storage_dir = self.storage_directory_path(sub_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            try:
                with open(file_path, 'rb') as file:
                    return BytesIO(file.read())
            except:
                logging.error(f"Failed to retreive file from local filesystem: {file_path}")
            return False
        else:
            try:
                tmp_file_path = RemoteStorage().get_object(sub_dir, storage_name)
                with open(tmp_file_path, 'rb') as file:
                    bytes = BytesIO(file.read())
                os.remove(tmp_file_path)
                return bytes
            except:
                file_path = f"{sub_dir}/{storage_name}"
                logging.error(f"Failed to retreive remote object: {file_path}")
                return False

    def delete_file(self, sub_dir, storage_name):
        if self.local_filesystem:
            local_storage_dir = self.storage_directory_path(sub_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            try:
                os.remove(file_path)
                return True
            except:
                logging.error(f"Failed to delete file from local filesystem: {file_path}")
            return False
        else:
            try:
                removed = RemoteStorage().delete_file(sub_dir, storage_name)
                if not removed:
                    logging.error(f"Failed to remove remote object: {file_path}")
                return removed
            except Exception as error:
                logging.error(error)
                return False
