"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


from mongoengine import QuerySet
from flask import g

class HostnameQuerySet(QuerySet):
    def ensure_hostname(self, **kwargs):
        if not g.is_root_user_enabled and not 'hostname' in kwargs:
            kwargs={'hostname':g.site.hostname, **kwargs}
        #print("ensure_hostname kwargs: %s" % kwargs)
        return self.filter(**kwargs)
