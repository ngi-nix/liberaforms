"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, json
import urllib3
from urllib.parse import urlparse
from flask import current_app, g



class FediPublisher():
    def publish(self, text, image=None):
        fedi_auth = g.current_user.fedi_auth
        http = urllib3.PoolManager()
        data = {
            "status": text,
            #"media_ids": [],
        }
        # https://mastodon.example/api/v1/statuses
        print(fedi_auth['node_url'])
        r = http.request(
            "POST",
            f"{fedi_auth['node_url']}/api/v1/statuses",
            body=json.dumps(data),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {fedi_auth['access_token']}"
            }
        )
        print(r.data)
