"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import smtplib, ssl, socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from email.header import Header
from threading import Thread

from flask import g, flash, request
from flask_babel import gettext

from liberaforms import app
from liberaforms.models.user import User

class EmailServer():
    server = None

    def __init__(self):
        config = g.site.smtpConfig
        if config["encryption"] == "SSL":
            try:
                self.server = smtplib.SMTP_SSL(config["host"], port=config["port"], timeout=7)
                self.server.login(config["user"], config["password"])
            except:
                self.server = None
        elif config["encryption"] == "STARTTLS":
            try:
                self.server = smtplib.SMTP_SSL(config["host"], port=config["port"], timeout=7)
                context = ssl.create_default_context()
                self.server.starttls(context=context)
                self.server.login(config["user"], config["password"])
            except:
                self.server = None
        else:
            try:
                self.server = smtplib.SMTP(config["host"], port=config["port"])
                if config["user"] and config["password"]:
                    self.server.login(config["user"], config["password"])
            except:
                self.server = None

    def closeConnection(self):
        if self.server:
            self.server.quit()

    def send(self, msg):
        if not self.server:
            return False
        try:
            msg['From'] = g.site.smtpConfig["noreplyAddress"]
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid()
            if not msg['Errors-To']:
                criteria={  'blocked': False,
                            'hostname': g.site.hostname,
                            'validatedEmail': True,
                            'isAdmin': True }
                admins=User.find_all(**criteria)
                if admins:
                    msg['Errors-To'] = g.site.get_admins()[0].email
            self.server.sendmail(msg['From'], msg['To'], msg.as_string())
            return True
        except Exception as e:
            if g.is_admin:
                flash(str(e) , 'error')
        return False

    def sendTestEmail(self, msg_to):
        msg = MIMEText(gettext("Congratulations!"), _subtype='plain', _charset='UTF-8')
        msg['Subject'] = Header(gettext("SMTP test")).encode()
        msg['To'] = msg_to
        msg['Errors-To'] = g.current_user.email
        state = self.send(msg)
        self.closeConnection()
        return state

    def sendInvite(self, invite):
        body = invite.get_message()
        msg = MIMEText(body, _subtype='plain', _charset='UTF-8')
        msg['Subject'] = Header(gettext("Invitation to %s" % invite.hostname)).encode()
        msg['To'] = invite.email
        state = self.send(msg)
        self.closeConnection()
        return state

    def sendNewUserNotification(self, user):
        emails=[]
        criteria={  'blocked': False,
                    'hostname': user.hostname,
                    'validatedEmail': True,
                    'isAdmin': True,
                    'notifyNewUser': True}
        admins=User.find_all(**criteria)
        for admin in admins:
            emails.append(admin['email'])
        body = gettext("New user '%s' created at %s" % (user.username, user.hostname))
        subject = Header(gettext("LiberaForms. New user notification")).encode()
        for msg_to in emails:
            msg = MIMEText(body, _subtype='plain', _charset='UTF-8')
            msg['Subject'] = subject
            msg['To'] = msg_to
            self.send(msg)
        self.closeConnection()

    def sendRecoverPassword(self, user):
        link = "%ssite/recover-password/%s" % (g.site.host_url, user.token['token'])
        body = "%s\n\n%s" % (gettext("Please use this link to recover your password"), link)
        msg = MIMEText(body, _subtype='plain', _charset='UTF-8')
        msg['Subject'] = Header(gettext("LiberaForms. Recover password")).encode()
        msg['To'] = user.email
        state = self.send(msg)
        self.closeConnection()
        return state

    def sendConfirmEmail(self, user, newEmail=None):
        link = "%suser/validate-email/%s" % (g.site.host_url, user.token['token'])
        body = gettext("Hello %s\n\nPlease confirm your email\n\n%s") % (user.username, link)
        msg = MIMEText(body, _subtype='plain', _charset='UTF-8')
        msg['Subject'] = Header(gettext("LiberaForms. Confirm email")).encode()
        msg['To'] = newEmail if newEmail else user.email
        state = self.send(msg)
        self.closeConnection()
        return state

    def sendNewFormNotification(self, form):
        emails=[]
        criteria={  'blocked': False,
                    'validatedEmail': True,
                    'isAdmin': True,
                    'notifyNewForm': True}
        admins=User.find_all(**criteria)
        for admin in admins:
            emails.append(admin.email)
        body = gettext("New form '%s' created at %s" % (form.slug, form.hostname))
        subject = Header(gettext("LiberaForms. New form notification")).encode()
        for msg_to in emails:
            msg = MIMEText(body, _subtype='plain', _charset='UTF-8')
            msg['Subject'] = subject
            msg['To'] = msg_to
            self.send(msg)
        self.closeConnection()

    def sendNewFormEntryNotification(self, emails, entry, slug):
        body = gettext("New form entry in %s at %s\n" % (slug, g.site.hostname))
        for data in entry:
            body = "%s\n%s: %s" % (body, data[0], data[1])
        body = "%s\n" % body
        subject = Header(gettext("LiberaForms. New form entry")).encode()
        for msg_to in emails:
            msg = MIMEText(body, _subtype='plain', _charset='UTF-8')
            msg['Subject'] = subject
            msg['To'] = msg_to
            self.send(msg)
        self.closeConnection()

    def sendConfirmation(self, msg_to, form):
        msg = MIMEMultipart('alternative')
        html_body=MIMEText(form.after_submit_text_html, _subtype='html', _charset='UTF-8')
        msg.attach(html_body)
        msg['Subject'] = Header(gettext("Confirmation message")).encode()
        msg['To'] = msg_to
        state = self.send(msg)
        self.closeConnection()
        return state

    def sendExpiredFormNotification(self, editorEmails, form):
        body = gettext("The form '%s' has expired at %s" % (form.slug, g.site.hostname))
        subject = Header(gettext("LiberaForms. A form has expired")).encode()
        for msg_to in editorEmails:
            msg = MIMEText(body, _subtype='plain', _charset='UTF-8')
            msg['Subject'] = subject
            msg['To'] = msg_to
            self.send(msg)
        self.closeConnection()
