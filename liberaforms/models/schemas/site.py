"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import ma
from liberaforms.models.site import Site


class SiteSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Site

    created = ma.auto_field()
    hostname = ma.auto_field()
