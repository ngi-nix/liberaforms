"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import ma
from liberaforms.models.media import Media
from liberaforms.utils import utils
from liberaforms.utils.utils import human_readable_bytes


class MediaSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Media

    id = ma.Integer()
    created = ma.Method('get_created')
    file_name = ma.auto_field()
    file_size = ma.Method('get_file_size')
    image_url =  ma.Method('get_image_url')
    thumbnail_url = ma.Method('get_thumbnail_url')
    alt_text = ma.auto_field()

    def get_created(self, obj):
        return utils.utc_to_g_timezone(obj.created).strftime("%Y-%m-%d")

    def get_image_url(self, obj):
        return obj.get_url()

    def get_thumbnail_url(self, obj):
        return obj.get_thumbnail_url()

    def get_file_size(self, obj):
        return human_readable_bytes(obj.file_size)
