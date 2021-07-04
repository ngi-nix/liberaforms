"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, jsonify
from liberaforms.models.form import Form
from liberaforms.models.schemas.form import FormSchema
from liberaforms.utils.wraps import *


form_api_bp = Blueprint('form_api_bp', __name__)


@form_api_bp.route('/api/forms', methods=['GET'])
@enabled_user_required_json
def all_forms():
    forms = Form.find_all(author_id=g.current_user.id)
    return jsonify(
        items=FormSchema(many=True).dump(forms),
        meta={'count': forms.count()}
    )
