"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json
import requests
from flask import current_app, g

#from pprint import pprint
# https://stackoverflow.com/questions/22346158/python-requests-how-to-limit-received-size-transfer-rate-and-or-total-time

ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


class FediPublisher():
    def publish(self, text, image_src=None):
        data = {
            "status": text,
        }
        if image_src:
            media_id = self._upload_media_to_node(image_src)
            if media_id:
                data['media_ids']=[media_id]
        fedi_auth = g.current_user.fedi_auth
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
        if not allowed_file(img_src):
            return None
        try:
            """ first download the media file
            """
            resp = requests.get(img_src)
            if resp.status_code != 200:
                msg = f"Could not get media: {img_src} {resp.status_code}"
                current_app.logger.warning(msg)
                return None
            file_bytes=resp.content

            """ upload the media file to the node
            """
            fedi_auth = g.current_user.fedi_auth
            endpoint = f"{fedi_auth['node_url']}/api/v1/media"
            resp = requests.post(
                endpoint,
                files={"file": file_bytes},
                headers={"Authorization": f"Bearer {fedi_auth['access_token']}"}
            )
            if resp.status_code != 200:
                msg = f"Could not post media: {endpoint} {resp.status_code}"
                current_app.logger.warning(msg)
                return None
            response = resp.json()
            return response['id'] if 'id' in response else None
        except Exception as error:
            current_app.logger.warning(error)
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
