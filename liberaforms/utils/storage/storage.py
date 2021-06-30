"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, shutil
from io import BytesIO
from flask import current_app
from liberaforms.utils.storage.remote import RemoteStorage
from liberaforms.utils.storage.crypto import encrypt_file, decrypt_file_content
from liberaforms.utils import utils


class Storage:
    def __init__(self):
        pass

    @staticmethod
    def get_local_storage_directory(sub_dir):
        return os.path.join(current_app.config['UPLOADS_DIR'], sub_dir)

    @staticmethod
    def get_remote_storage_path(sub_dir):
        if 'FQDN' in os.environ:
            """ Part of this path is set in config.py to be used with
                local filesystem storage. We remove 'hosts/FQDN' because the
                buckets are root objects and uniquely identified by their FQDN
            """
            return sub_dir.replace(f"/hosts/{os.environ['FQDN']}", "")
        return sub_dir

    def save_to_disk(self, tmp_file_path, sub_dir, storage_name):
        local_storage_dir = self.get_local_storage_directory(sub_dir)
        try:
            if not os.path.exists(local_storage_dir):
                os.makedirs(local_storage_dir)
            dest_file_path = os.path.join(local_storage_dir, storage_name)
            shutil.move(tmp_file_path, dest_file_path)
            return True
        except Exception as error:
            current_app.logger.error(f"Failed to save file to local filesystem: {error}")
            self.delete_from_disk(tmp_file_path)
            return False

    @staticmethod
    def delete_from_disk(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        else:
            current_app.logger.error(f"Failed to delete file. Does not exist: {file_path}")
            return False

    def save_file(self, file, storage_name, sub_dir):
        tmp_dir = current_app.config['TMP_DIR']
        tmp_file_path = f"{tmp_dir}/{storage_name}"
        if not os.path.exists(tmp_file_path):
            try:
                file.save(tmp_file_path)
            except Exception as error:
                current_app.logger.error(f"Cannot save to tmp_file. : {error}")
                return False
        file_size = os.path.getsize(tmp_file_path)
        self.file_size = utils.human_readable_bytes(file_size)
        if sub_dir.startswith('attachment'):
            """ attachments get encrypted """
            enc_file_path = encrypt_file(tmp_file_path)
            if enc_file_path:
                self.encrypted=True
                self.delete_from_disk(tmp_file_path)
                tmp_file_path = enc_file_path
            else:
                current_app.logger.info(f"Failed to encrypt attachment: {sub_dir}")
        if current_app.config['ENABLE_REMOTE_STORAGE']:
            saved = RemoteStorage().add_object(
                                    tmp_file_path,
                                    self.get_remote_storage_path(sub_dir),
                                    storage_name
                                    )
            if saved == True:
                self.local_filesystem = False
                self.delete_from_disk(tmp_file_path)
                return True
            else:
                current_app.logger.warning(f"Failed to save remote object. Saving to local filesystem.")
                saved = self.save_to_disk(tmp_file_path, sub_dir, storage_name)
                if saved == True:
                    return True
                else:
                    file_path = f"{sub_dir}/{storage_name}"
                    current_app.logger.error(f"Did not save file: {file_path}")
                    return False
        else:
            saved = self.save_to_disk(tmp_file_path, sub_dir, storage_name)
            if saved == True:
                return True
            else:
                file_path = f"{sub_dir}/{storage_name}"
                current_app.logger.error(f"Upload failed. Did not save file: {file_path}")
                return False
        return False

    def get_file(self, storage_name, sub_dir):
        file_content = None
        if self.local_filesystem:
            local_storage_dir = self.get_local_storage_directory(sub_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            try:
                with open(file_path, 'rb') as file:
                    file_content = file.read()
            except:
                current_app.logger.error(f"Failed to retrieve file from local filesystem: {file_path}")
                return None
        else:
            try:
                tmp_file_path = RemoteStorage().get_object(
                                        self.get_remote_storage_path(sub_dir),
                                        storage_name)
                if not tmp_file_path:
                    return None
                with open(tmp_file_path, 'rb') as file:
                    file_content = file.read()
                self.delete_from_disk(tmp_file_path)
            except:
                file_path = f"{sub_dir}/{storage_name}"
                current_app.logger.error(f"Failed to retrieve remote object: {file_path}")
                return None
        if not file_content:
            return None
        if self.encrypted:
            file_content = decrypt_file_content(file_content)
        return BytesIO(file_content)

    def does_file_exist(self, sub_dir, storage_name):
        if self.local_filesystem:
            local_storage_dir = self.get_local_storage_directory(sub_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            return os.path.exists(file_path)
        else:
            remote_dir = self.get_remote_storage_path(sub_dir)
            directory_content = RemoteStorage().list_directory(remote_dir)
            for object in directory_content:
                if storage_name in object.object_name:
                    return True
            return False

    def delete_file(self, storage_name, sub_dir):
        if self.local_filesystem:
            local_storage_dir = self.get_local_storage_directory(sub_dir)
            file_path = os.path.join(local_storage_dir, storage_name)
            return self.delete_from_disk(file_path)
        else:
            try:
                removed = RemoteStorage().delete_file(
                                            self.get_remote_storage_path(sub_dir),
                                            storage_name)
                if not removed:
                    file_path = f"{sub_dir}/{storage_name}"
                    current_app.logger.error(f"Failed to remove remote object: {file_path}")
                return removed
            except Exception as error:
                current_app.logger.error(error)
                return False
