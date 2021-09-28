"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import ma
from liberaforms.models.user import User
from liberaforms.models.formuser import FormUser


class UserSchemaForAdminDataDisplay(ma.SQLAlchemySchema):
    class Meta:
        model = User

    id = ma.auto_field()
    created = ma.auto_field()
    username = ma.auto_field()
    email = ma.auto_field()
    enabled = ma.Method('get_is_enabled')
    is_admin = ma.Method('get_is_admin')
    total_forms = ma.Method('get_total_forms')

    def get_is_enabled(self, obj):
        return obj.enabled

    def get_total_forms(self, obj):
        return FormUser.find_all(user_id=obj.id).count()

    def get_is_admin(self, obj):
        return obj.is_admin()
