"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""


from mongoengine import QuerySet
from flask import g

class HostnameQuerySet(QuerySet):
    def ensure_hostname(self, **kwargs):
        if not g.is_root_user_enabled and not 'hostname' in kwargs:
            kwargs={'hostname':g.site.hostname, **kwargs}
        #print("ensure_hostname kwargs: %s" % kwargs)
        return self.filter(**kwargs)
