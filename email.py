"""
“Copyright 2019 La Coordinadora d’Entitats la Lleialtat Santsenca”

This file is part of GNGforms.

GNGforms is free software: you can redistribute it and/or modify
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

from formbuilder import app
import smtplib
from .persitence import Site

import pprint


def smtpSendConfirmEmail(user, subject):
    link="%suser/validate-email/%s" % (request.url_root, user.token['token'])
    body="Hello %s\n\nPlease confirm your email\n\n%s" % (user['username'], link)

    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(Site().noreplyEmailAddress, user.email, body)         
        return True
    except SMTPException:
        return False
