"""
“Copyright 2019 La Coordinadora d’Entitats per la Lleialtat Santsenca”

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

from flask import flash, request
from flask_babel import gettext
from GNGforms import app
import smtplib, socket
from .persitence import Site

import pprint


def createSmtpObj():
    try:
        smtpObj = smtplib.SMTP(app.config['SMTP_SERVER'])
        return smtpObj
    except socket.error as e:
        flash(gettext("Could not connect to SMTP server"), 'error')
        return False        


def sendMail(email, body):
    smtpObj = createSmtpObj()
    if smtpObj:
        try:
            smtpObj.sendmail(Site().noreplyEmailAddress, email, body)         
            return True
        except:
            pass
    return False


def smtpSendConfirmEmail(user):
    link="%suser/validate-email/%s" % (request.url_root, user.token['token'])
    body="Hello %s\n\nPlease confirm your email\n\n%s" % (user.username, link)

    #print(body)
    return sendMail(user.email, body)


def smtpSendInvite(invite):
    link="%suser/new/%s" % (request.url_root, invite.data['token']['token'])
    body="%s\n\n%s" % (invite.data['message'], link)
      
    print(body)
    return sendMail(invite.data['email'], body)
    

def smtpSendRecoverPassword(user):
    link="%ssite/recover-password/%s" % (request.url_root, user.token['token'])
    body="Please use this link to recover your password"
    body="%s\n\n%s" % (body, link)
    
    return sendMail(user.email, body)


def smtpSendTestEmail(email):
    body="Congratulations!"
    
    return sendMail(email, body)
