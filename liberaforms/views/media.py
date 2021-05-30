"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import json, logging
from flask import g, request, render_template, redirect
from flask import Blueprint, current_app
from flask import flash
from flask_babel import gettext as _

from liberaforms.models.media import Media
from liberaforms.utils.wraps import *
from liberaforms.utils.utils import make_url_for, JsonResponse
from liberaforms.utils import validators

from pprint import pprint

media_bp = Blueprint('media_bp',
                    __name__,
                    template_folder='../templates/media')


@media_bp.route('/media/save', methods=['POST'])
@enabled_user_required
def save_media():
    if not (current_app.config['ENABLE_UPLOADS'] and request.files['file']):
        return JsonResponse(json.dumps({"image_url": ""}))
    file = request.files['file']
    # TODO: check mimetype and size first
    media = Media()
    saved = media.save_media(g.current_user,
                             file,
                             request.form['alt_text'])
    if saved:
        return JsonResponse(json.dumps(media.get_values()))
    return JsonResponse(json.dumps(False))

@media_bp.route('/media/<string:username>', methods=['GET'])
@enabled_user_required
def list_media(username):
    #media = Media.find_all(user_id=g.current_user.id)
    return render_template('list-media.html')

@media_bp.route('/media/delete/<int:media_id>', methods=['POST'])
@enabled_user_required
def remove_media(media_id):
    media = Media.find(id=media_id, user_id=g.current_user.id)
    if media:
        removed = media.delete_media()
        if removed:
            return JsonResponse(json.dumps(media.id))
    return JsonResponse(json.dumps(False))

@media_bp.route('/media/get-values/<int:media_id>', methods=['GET'])
@enabled_user_required
def get_values(media_id):
    media = Media.find(id=media_id, user_id=g.current_user.id)
    if media:
        return JsonResponse(json.dumps(media.get_values()))
    return JsonResponse(json.dumps(False))
