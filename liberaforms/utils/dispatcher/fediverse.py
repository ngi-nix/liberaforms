"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json
import requests
from pathlib import Path
from flask import current_app, g
from liberaforms.utils import utils

#from pprint import pprint

ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


class FediPublisher():
    def publish(self, text, image_src=None):
        data = {
            "status": text,
        }
        if image_src:
            media_id = self._upload_media_to_node(image_src)
            if media_id:
                data['media_ids']=[media_id]
        fedi_auth = g.current_user.get_fedi_auth()
        try:
            endpoint = f"{fedi_auth['node_url']}/api/v1/statuses"
            resp = requests.post(
                endpoint,
                json=data,
                headers={"Authorization": f"Bearer {fedi_auth['access_token']}"}
            )
            if resp.status_code != 200:
                msg = f"Could not post status: {endpoint} {resp.status_code}"
                current_app.logger.warning(msg)
                return False, msg
            resp = resp.json()
            return True, resp['url']
        except Exception as error:
            current_app.logger.warning(error)
            return False, error

    def _upload_media_to_node(self, img_src):
        filename = Path(img_src).name
        if '.' in filename:
            file_extension = filename.rsplit('.', 1)[1].lower()
        else:
            return None
        if not file_extension in ALLOWED_IMAGE_EXTENSIONS:
            return None

        """ first download the media file
        """
        tmp_filename = f"{utils.gen_random_string()}.{file_extension}"
        tmp_filepath = os.path.join(current_app.config['TMP_DIR'],
                                    tmp_filename)
        resp = requests.get(img_src, stream=True)
        if resp.status_code != 200:
            msg = f"Could not get media: {img_src} {resp.status_code}"
            current_app.logger.warning(msg)
            return None
        try:
            with open(tmp_filepath, 'wb') as f:
                size = 0
                for chunk in resp.iter_content(1024):
                    size += len(chunk)
                    if size > current_app.config['MAX_MEDIA_SIZE']:
                        resp.close()
                        raise
                    f.write(chunk)
        except:
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)
            return None

        """ upload the media file to the node
        """
        fedi_auth = g.current_user.get_fedi_auth()
        endpoint = f"{fedi_auth['node_url']}/api/v1/media"
        try:
            with open(tmp_filepath, 'rb') as f:
                resp = requests.post(
                    endpoint,
                    files={"file": f},
                    headers={"Authorization": f"Bearer {fedi_auth['access_token']}"}
                )
            os.remove(tmp_filepath)
            if resp.status_code != 200:
                msg = f"Could not post media: {endpoint} {resp.status_code}"
                current_app.logger.warning(msg)
                return None
            response = resp.json()
            return response['id'] if 'id' in response else None
        except Exception as error:
            current_app.logger.warning(error)
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)
            return None


"""
def get_node_info(node_url):
    try:
        # test for pleroma instance
        #
        resp = requests.get(f'{node_url}/nodeinfo/2.0.json')
        resp = resp.json()
        if resp['software']['name'] == 'pleroma':
            return {"instance_of": resp['software']['name'],
                    "version": resp['version']}
    except Exception as error:
        current_app.logger.warning(error)
    try:
        # test for mastodon instance
        #
        resp = requests.get(f'{node_url}/api/v1/instance')
        resp = resp.json()
        # Guessing this is mastodon. No reliable software_name field
        return {"instance_of": "mastodon",
                "version": resp['version']}
    except Exception as error:
        current_app.logger.warning(error)
    return None
"""
