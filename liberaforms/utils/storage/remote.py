"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import sys, os, logging
from io import BytesIO
from flask import current_app
from minio import Minio
from minio.error import S3Error
from liberaforms.utils import utils

#https://docs.min.io/docs/python-client-api-reference.html

class RemoteStorage():
    client = None
    bucket_name = None
    region = None

    def __init__(self):
        self.region = 'eu-central-1'
        try:
            self.client = Minio(
                    f"{current_app.config['MINIO_HOST']}:9000",
                    access_key=current_app.config['MINIO_ACCESS_KEY'],
                    secret_key=current_app.config['MINIO_SECRET_KEY'],
                    #region=self.region,
                    secure=False,
            )
        except S3Error as error:
            logging.error(error)
            self.client = None
            return
        from liberaforms.models.site import Site
        self.bucket_name = Site.find().hostname
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as error:
            logging.error(error)
            self.client = None

    def add_object(self, file_path, directory, storage_name):
        if not self.client:
            return False
        try:
            result = self.client.fput_object(
                            bucket_name=self.bucket_name,
                            object_name=f"{directory}/{storage_name}",
                            file_path=file_path
            )
            return True
        except S3Error as error:
            logging.error(error)
            return False

    def remove_object(self, directory, storage_name):
        try:
            self.client.remove_object(
                            bucket_name=self.bucket_name,
                            object_name=f"{directory}/{storage_name}",
                        )
            return True
        except S3Error as error:
            logging.error(error)
            return False
