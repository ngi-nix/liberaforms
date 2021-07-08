"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, request, jsonify
from flask_babel import gettext as _
from liberaforms.models.site import Site
from liberaforms.models.form import Form
from liberaforms.models.schemas.site import SiteSchema
from liberaforms.models.schemas.form import FormSchema
from liberaforms.utils import utils
from liberaforms.utils.wraps import *

api_bp = Blueprint('api_bp', __name__)


""" Unsensitve site information only
"""
@api_bp.route('/api/site/info', methods=['GET'])
#@enabled_user_required__json
def site_info():
    site=SiteSchema(only=['created',
                          'hostname']).dump(Site.find())
    site['version'] = utils.get_app_version()
    return jsonify(
        site=site
    ), 200


""" Public available form information only
"""
@api_bp.route('/api/form/<int:form_id>/info', methods=['GET'])
def form_info(form_id):
    form = Form.find(id=form_id)
    if not (form and form.is_public()):
        return jsonify("Denied"), 401
    return jsonify(
        form=FormSchema(only=['slug',
                              'created',
                              'introduction_md',
                              'structure']).dump(form)
    ), 200
