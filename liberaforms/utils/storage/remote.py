"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import sys, os, logging
import urllib3
from threading import Thread
from flask import current_app
from minio import Minio
from minio.deleteobjects import DeleteObject
from minio.error import S3Error
from liberaforms.utils import utils

#https://docs.min.io/docs/python-client-api-reference.html
#https://urllib3.readthedocs.io/en/latest/reference/urllib3.exceptions.html

def get_minio_client():
    try:
        return Minio(
                os.environ['MINIO_HOST'],
                access_key=os.environ['MINIO_ACCESS_KEY'],
                secret_key=os.environ['MINIO_SECRET_KEY'],
                #region=self.region,
                secure=False,
                http_client=urllib3.PoolManager(
                    timeout=2,
                    #timeout=urllib3.Timeout.DEFAULT_TIMEOUT,
                    #cert_reqs="CERT_REQUIRED",
                    retries=urllib3.Retry(
                        total=2,
                        backoff_factor=0.2,
                        status_forcelist=[500, 502, 503, 504],
                    ),
                )
        )
    except S3Error as error:
        logging.error(error)
    except HTTPError:
        logging.error(error)
    except urllib3.exceptions.ConnectTimeoutError as error:
        logging.error(error)
    except urllib3.exceptions.MaxRetryError as error:
        logging.error(error)
    except urllib3.exceptions.NewConnectionError as error:
        logging.error(error)
    except urllib3.exceptions.ProtocolError as error:
        logging.error(error)
    except Exception as error:
        logging.error(error)
    return None

class RemoteStorage():
    client = None
    bucket_name = None
    region = None

    def __init__(self):
        from liberaforms.models.site import Site
        self.region = 'eu-central-1'
        self.bucket_name = Site.find().hostname

    def ensure_bucket_exists(self):
        try:
            client = get_minio_client()
            if not client.bucket_exists(self.bucket_name):
                client.make_bucket(self.bucket_name)
            return client.bucket_exists(self.bucket_name)
        except S3Error as error:
            logging.error(error)
            return False

    def add_object(self, file_path, directory, storage_name):
        try:
            client = get_minio_client()
            result =client.fput_object(
                            bucket_name=self.bucket_name,
                            object_name=f"{directory}/{storage_name}",
                            file_path=file_path
            )
            return True
        except S3Error as error:
            logging.error(error)
            return False

    def get_object(self, directory, storage_name):
        try:
            tmp_dir = current_app.config['TMP_DIR']
            file_path = f"{tmp_dir}/{storage_name}"
            client = get_minio_client()
            client.fget_object(
                            bucket_name=self.bucket_name,
                            object_name=f"{directory}/{storage_name}",
                            file_path=file_path
            )
            return file_path
        except S3Error as error:
            logging.error(error)
            return False

    def remove_object(self, app, directory, storage_name):
        with app.app_context():
            try:
                client = get_minio_client()
                client.remove_object(
                                bucket_name=self.bucket_name,
                                object_name=f"{directory}/{storage_name}",
                            )
                return True
            except S3Error as error:
                logging.error(error)
                return False

    def delete_file(self, directory, storage_name):
        thr = Thread(
                target=self.remove_object,
                args=[current_app._get_current_object(), directory, storage_name]
        )
        thr.start()

    def delete_objects(self, app, prefix):
        with app.app_context():
            client = get_minio_client()
            delete_object_list = map(
                lambda x: DeleteObject(x.object_name),
                client.list_objects(
                            bucket_name=self.bucket_name,
                            prefix=prefix,
                            recursive=True
                        )
            )
            errors = client.remove_objects(
                            bucket_name=self.bucket_name,
                            delete_object_list=delete_object_list,
                        )
            for error in errors:
                logging.error(error)

    def remove_directory(self, prefix):
        thr = Thread(
                target=self.delete_objects,
                args=[current_app._get_current_object(), prefix]
        )
        thr.start()
