"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import json
from flask import g, request, render_template, redirect
from flask import Blueprint, current_app, jsonify
from flask import flash
from flask_babel import gettext as _
from liberaforms.models.media import Media
from liberaforms.models.schemas.media import MediaSchema
from liberaforms.utils.wraps import *
from liberaforms.utils.utils import make_url_for, JsonResponse, human_readable_bytes
from liberaforms.utils import wtf
from liberaforms.utils import validators

from pprint import pprint

media_bp = Blueprint('media_bp',
                    __name__,
                    template_folder='../templates/media')


@media_bp.route('/media/save', methods=['POST'])
@enabled_user_required
def save_media():
    if not (current_app.config['ENABLE_UPLOADS']):
        return JsonResponse(json.dumps({"image_url": ""}))
    wtform = wtf.UploadMedia()
    if not wtform.validate_on_submit():
        errors = wtform.errors
        return JsonResponse(json.dumps({"errors": errors}))
    media = Media()
    saved = media.save_media(g.current_user,
                             request.files['media_file'],
                             request.form['alt_text'])
    if saved:
        total_usage=g.current_user.total_uploads_usage()
        percent="{:.2f} %".format((total_usage * 100) / g.current_user.uploads_limit)
        return jsonify(
            media=MediaSchema().dump(media),
            usage_percent=percent,
            total_usage=total_usage
        ), 200
    return JsonResponse(json.dumps(False))

@media_bp.route('/user/<string:username>/media', methods=['GET'])
@enabled_user_required
def list_media(username):
    if username != g.current_user.username:
        return redirect(make_url_for(
                                'media_bp.list_media',
                                 username=g.current_user.username)
                        )
    if not g.current_user.uploads_enabled:
        return redirect(make_url_for(
                                'user_bp.user_settings',
                                 username=g.current_user.username)
                        )
    return render_template('list-media.html',
                            human_readable_bytes=human_readable_bytes,
                            user=g.current_user,
                            wtform=wtf.UploadMedia())

@media_bp.route('/media/delete/<int:media_id>', methods=['POST'])
@enabled_user_required__json
def remove_media(media_id):
    media = Media.find(id=media_id, user_id=g.current_user.id)
    if media:
        removed = media.delete_media()
        if removed:
            total_usage=g.current_user.total_uploads_usage()
            percent="{:.2f} %".format((total_usage * 100) / g.current_user.uploads_limit)
            return jsonify(
                media_id=media.id,
                usage_percent=percent,
                total_usage=total_usage
            ), 200
    return JsonResponse(json.dumps(False))

@media_bp.route('/media/get-values/<int:media_id>', methods=['GET'])
@enabled_user_required
def get_values(media_id):
    media = Media.find(id=media_id, user_id=g.current_user.id)
    if media:
        return jsonify(
            media=MediaSchema().dump(media)
        ), 200
    return JsonResponse(json.dumps(False))
