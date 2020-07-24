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
import smtplib, ssl, socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread

from gngforms import app
from gngforms.models import Site, User

def createSmtpObj():
    config=g.site.smtpConfig
    try:
        if config["encryption"] == "SSL":
            server = smtplib.SMTP_SSL(config["host"], port=config["port"], timeout=2)
            server.login(config["user"], config["password"])
            
        elif config["encryption"] == "STARTTLS":
            server = smtplib.SMTP_SSL(config["host"], port=config["port"], timeout=2)
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.login(config["user"], config["password"])
            
        else:
            server = smtplib.SMTP(config["host"], port=config["port"])
            if config["user"] and config["password"]:
                server.login(config["user"], config["password"])
        
        return server
    except socket.error as e:
        if g.isAdmin:
            flash(str(e), 'error')
        return False        

def sendMail(email, message):
    server = createSmtpObj()
    if server:
        try:
            if type(message).__name__ == 'MIMEMultipart':
                message['To']=email
                message['From']=g.site.smtpConfig["noreplyAddress"]
                message=message.as_string()
            else:
                header='To: ' + email + '\n' + 'From: ' + g.site.smtpConfig["noreplyAddress"] + '\n'
                message=header + message                  
            server.sendmail(g.site.smtpConfig["noreplyAddress"], email, message.encode('utf-8'))
            return True
        except Exception as e:
            if g.isAdmin:
                flash(str(e) , 'error')
    return False

def sendConfirmEmail(user, newEmail=None):
    link="%suser/validate-email/%s" % (g.site.host_url, user.token['token'])
    message=gettext("Hello %s\n\nPlease confirm your email\n\n%s") % (user.username, link)
    message = 'Subject: {}\n\n{}'.format(gettext("GNGforms. Confirm email"), message)
    if newEmail:
        return sendMail(newEmail, message)
    else:
        return sendMail(user.email, message)

def sendInvite(invite):
    message=invite.getMessage()
    message='Subject: {}\n\n{}'.format(gettext("Invitation to %s" % invite.hostname), message)
    return sendMail(invite.email, message)
    
def sendRecoverPassword(user):
    link="%ssite/recover-password/%s" % (g.site.host_url, user.token['token'])
    message=gettext("Please use this link to recover your password")
    message="%s\n\n%s" % (message, link)
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. Recover password"), message)
    return sendMail(user.email, message)

def sendNewFormEntryNotification(emails, entry, slug):
    message=gettext("New form entry in %s at %s\n" % (slug, g.site.hostname))
    for data in entry:
        message="%s\n%s: %s" % (message, data[0], data[1])
    message="%s\n" % message
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. New form entry"), message)
    for email in emails:
        sendMail(email, message)

def sendExpiredFormNotification(editorEmails, form):
    message=gettext("The form '%s' has expired at %s" % (form.slug, g.site.hostname))
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. A form has expired"), message)
    for email in editorEmails:
        sendMail(email, message)
    
def sendNewFormNotification(form):
    emails=[]
    criteria={  'blocked':False,
                'hostname': form.hostname,
                'validatedEmail':True,
                'admin__isAdmin':True,
                'admin__notifyNewForm':True}
    admins=User.findAll(**criteria)
    for admin in admins:
        emails.append(admin['email'])
    rootUsers=User.objects(__raw__={'email': {"$in": app.config['ROOT_USERS']},
                                    'admin.notifyNewForm':True})
    for rootUser in rootUsers:
        if not rootUser['email'] in emails:
            emails.append(rootUser['email'])

    message=gettext("New form '%s' created at %s" % (form.slug, form.hostname))
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. New form notification"), message)
    for email in emails:
        sendMail(email, message)


def sendNewUserNotification(user):
    emails=[]
    criteria={  'blocked':False,
                'hostname': user.hostname,
                'validatedEmail': True,
                'admin__isAdmin':True,
                'admin__notifyNewUser':True}
    admins=User.findAll(**criteria)
    for admin in admins:
        emails.append(admin['email'])
    rootUsers=User.objects(__raw__={'email':{"$in": app.config['ROOT_USERS']},
                                    'admin.notifyNewUser':True})
    for rootUser in rootUsers:
        if not rootUser['email'] in emails:
            emails.append(rootUser['email'])

    message=gettext("New user '%s' created at %s" % (user.username, user.hostname))
    message='Subject: {}\n\n{}'.format(gettext("GNGforms. New user notification"), message)    
    for email in emails:
        sendMail(email, message)

def sendConfirmation(email, form):
    message = MIMEMultipart('alternative')
    html_body=MIMEText(form.afterSubmitTextHTML, 'html')
    message.attach(html_body)
    message['Subject'] = gettext("Confirmation message")
    return sendMail(email, message)
    
def sendTestEmail(email):
    message=gettext("Congratulations!")
    message='Subject: {}\n\n{}'.format(gettext("SMTP test"), message)
    return sendMail(email, message)
