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

from flask import g, flash, request
from flask_babel import gettext
from GNGforms import app
import smtplib, socket
from .persitence import Site


def createSmtpObj():
    try:
        smtpObj = smtplib.SMTP(app.config['SMTP_SERVER'])
        return smtpObj
    except socket.error as e:
        if g.isAdmin:
            flash(gettext("Could not connect to SMTP server"), 'error')
        return False        


def sendMail(email, message):
    smtpObj = createSmtpObj()
    if smtpObj:
        try:
            smtpObj.sendmail(Site().noreplyEmailAddress, email, message)         
            return True
        except:
            pass
    return False


def smtpSendConfirmEmail(user, newEmail=None):
    link="%suser/validate-email/%s" % (Site().host_url, user.token['token'])
    message=gettext("Hello %s\n\nPlease confirm your email\n\n%s") % (user.username, link)
    message = 'Subject: {}\n\n{}'.format(gettext("GNGforms. Confirm email"), message)

    if newEmail:
        return sendMail(newEmail, message)
    else:
        return sendMail(user.email, message)


def smtpSendInvite(invite):
    site=Site(hostname=invite.data['hostname'])
    link="%suser/new/%s" % (site.host_url, invite.data['token']['token'])
    message="%s\n\n%s" % (invite.data['message'], link)   
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. Invitation to %s" % site.hostname), message)
      
    #print(message)
    return sendMail(invite.data['email'], message)
    

def smtpSendRecoverPassword(user):
    link="%ssite/recover-password/%s" % (Site().host_url, user.token['token'])
    message=gettext("Please use this link to recover your password")
    message="%s\n\n%s" % (message, link)
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. Recover password"), message)
    
    return sendMail(user.email, message)


def smtpSendNewFormEntryNotification(email, entry, slug):
    message=gettext("New form entry in %s at %s\n" % (slug, Site().hostname))
    for data in entry:
        message="%s\n%s: %s" % (message, data[0], data[1])

    message='Subject: {}\n\n{}'.format(gettext("GNGforms. New form entry"), message)
    
    sendMail(email, message)

def smtpSendNewFormNotification(adminEmails, form):
    message=gettext("New form '%s' created at %s" % (form.slug, Site().hostname))
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. New form notification"), message)
    
    for email in adminEmails:
        sendMail(email, message)

def smtpSendNewUserNotification(adminEmails, username):
    message=gettext("New user '%s' created at %s" % (username, Site().hostname))
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. New user notification"), message)
    
    for email in adminEmails:
        sendMail(email, message)


def smtpSendTestEmail(email):
    message=gettext("Congratulations!")
    message='Subject: {}\n\n{}'.format(gettext("SMTP test"), message)
    
    return sendMail(email, message)
