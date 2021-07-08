"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import sys, os
import urllib3
from urllib.parse import urlparse
from threading import Thread
from flask import current_app
from minio import Minio
from minio.deleteobjects import DeleteObject
from minio.error import S3Error
from jinja2 import Environment, FileSystemLoader
from liberaforms.utils import utils

#https://docs.min.io/docs/python-client-api-reference.html
#https://urllib3.readthedocs.io/en/latest/reference/urllib3.exceptions.html

def get_minio_client():
    try:
        parsed_url = urlparse(os.environ['MINIO_URL'])
        return Minio(
                parsed_url.netloc,
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
        current_app.logger.error(error)
    except HTTPError:
        current_app.logger.error(error)
    except urllib3.exceptions.ConnectTimeoutError as error:
        current_app.logger.error(error)
    except urllib3.exceptions.MaxRetryError as error:
        current_app.logger.error(error)
    except urllib3.exceptions.NewConnectionError as error:
        current_app.logger.error(error)
    except urllib3.exceptions.ProtocolError as error:
        current_app.logger.error(error)
    except Exception as error:
        current_app.logger.error(error)
    return None

def generate_bucket_policy(template, bucket_name):
    template_dir = os.path.join(current_app.root_path, 'utils/storage/policies')
    j2_env = Environment(loader = FileSystemLoader(template_dir))
    j2_template = j2_env.get_template(template)
    return j2_template.render(bucket_name=bucket_name)


class RemoteStorage():
    hostname = None
    attachment_bucket_name = None
    media_bucket_name = None

    def __init__(self):
        from liberaforms.models.site import Site
        site = Site.query.first()
        if site:
            self.hostname = site.hostname
            self.attachment_bucket_name = f"{self.hostname}.attachments"
            self.media_bucket_name = f"{self.hostname}.media"
        else:
            current_app.logger.error("Cannot initiate RemoteStorage. Site does not exist")

    def get_bucket_name_and_prefix(self, object_path):
        if object_path.startswith('attachments'):
            return  self.attachment_bucket_name, \
                    object_path.lstrip('attachments')
        if object_path.startswith('media'):
            return  self.media_bucket_name, \
                    object_path.lstrip('media')
        current_app.logger.error("Could not resolve bucket_name")
        return None, None

    def get_existing_bucket_names(self, client=None):
        if not client:
            client = get_minio_client()
        bucket_names = [bucket.name for bucket in client.list_buckets()]
        names = []
        if self.attachment_bucket_name in bucket_names:
            names.append(self.attachment_bucket_name)
        if self.media_bucket_name in bucket_names:
            names.append(self.media_bucket_name)
        return names

    def do_buckets_exist(self, client=None):
        if not self.hostname:
            return False
        if not client:
            client = get_minio_client()
        if len(self.get_existing_bucket_names(client)) == 2:
            return True
        else:
            return False

    def create_buckets(self):
        if not self.hostname:
            return False, "Site does not exist. Please create storage."
        try:
            client = get_minio_client()
            bucket_names = self.get_existing_bucket_names(client)
            if len(bucket_names) == 2:
                return True, f"Both buckets already exist for: {self.hostname}"
            if not self.attachment_bucket_name in bucket_names:
                client.make_bucket(self.attachment_bucket_name)
            if not self.media_bucket_name in bucket_names:
                client.make_bucket(self.media_bucket_name)
                # set anonymous download permission on bucket
                policy = generate_bucket_policy('read_only.j2',
                                                self.media_bucket_name)
                client.set_bucket_policy(self.media_bucket_name, policy)
            if self.do_buckets_exist(client):
                return True, f"Both buckets ready for: {self.hostname}"
            return False, "Could not create buckets."
        except S3Error as error:
            current_app.logger.error(error)
            return False, str(error)

    def add_object(self, filesystem_path, object_path, storage_name):
        try:
            client = get_minio_client()
            (bucket_name, prefix) = self.get_bucket_name_and_prefix(object_path)
            result =client.fput_object(
                            bucket_name=bucket_name,
                            object_name=f"{prefix}/{storage_name}",
                            file_path=filesystem_path
            )
            return True
        except S3Error as error:
            current_app.logger.error(error)
            return False

    def get_object(self, object_path, storage_name):
        try:
            tmp_dir = current_app.config['TMP_DIR']
            file_path = f"{tmp_dir}/{storage_name}"
            client = get_minio_client()
            (bucket_name, prefix) = self.get_bucket_name_and_prefix(object_path)
            client.fget_object(
                            bucket_name=bucket_name,
                            object_name=f"{prefix}/{storage_name}",
                            file_path=file_path
            )
            return file_path
        except S3Error as error:
            current_app.logger.error(error)
            return False

    def remove_object(self, object_path, storage_name):
        try:
            client = get_minio_client()
            (bucket_name, prefix) = self.get_bucket_name_and_prefix(object_path)
            client.remove_object(
                            bucket_name=bucket_name,
                            object_name=f"{prefix}/{storage_name}",
                        )
            return True
        except S3Error as error:
            current_app.logger.error(error)
            return False

    def list_directory(self, object_path):
        client = get_minio_client()
        (bucket_name, prefix) = self.get_bucket_name_and_prefix(object_path)
        return client.list_objects(bucket_name, prefix=prefix, recursive=True)

    def delete_file(self, object_path, storage_name):
        return self.remove_object(object_path, storage_name)

    def delete_objects(self, object_path):
        client = get_minio_client()
        (bucket_name, prefix) = self.get_bucket_name_and_prefix(object_path)
        delete_object_list = map(
            lambda x: DeleteObject(x.object_name),
            client.list_objects(
                        bucket_name=bucket_name,
                        prefix=prefix,
                        recursive=True
                    )
        )
        errors = client.remove_objects(
                        bucket_name=bucket_name,
                        delete_object_list=delete_object_list,
                    )
        for error in errors:
            current_app.logger.error(error)

    def remove_directory(self, object_path):
        return self.delete_objects( object_path)
