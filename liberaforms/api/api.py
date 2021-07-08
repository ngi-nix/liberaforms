"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, request, jsonify
from flask_babel import gettext as _
from liberaforms.models.site import Site
from liberaforms.models.schemas.site import SiteSchema
from liberaforms.utils import utils
from liberaforms.utils.wraps import *

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/api/site', methods=['GET'])
#@enabled_user_required__json
def site_info():

    site=SiteSchema().dump(Site.find())
    site['version'] = utils.get_app_version()
    return jsonify(
        site=site
    ), 200
