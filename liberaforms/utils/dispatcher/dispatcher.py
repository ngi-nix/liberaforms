"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
from flask import current_app, g
from flask_babel import gettext as _
from jinja2 import Environment, FileSystemLoader
from threading import Thread

from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from mjml.mjml2html import mjml_to_html
from liberaforms.models.site import Site
from liberaforms.models.user import User
from liberaforms.utils.dispatcher.email import EmailServer
from liberaforms.utils.dispatcher.fediverse import FediPublisher



def HTML_email(template_file, **kwargs):
    template_dir = os.path.join(current_app.root_path, 'utils/dispatcher/templates')
    j2_env = Environment(loader = FileSystemLoader(template_dir))
    j2_template = j2_env.get_template(template_file)
    kwargs['body'] = kwargs['body'].replace('\n', '<br />')
    mjml_template = j2_template.render(kwargs)
    result = mjml_to_html(mjml_template)
    return result.html

def branding_body_preview():
    body="Lorem ipsum dolor sit amet, consectetur \
          adipisci elit, sed eiusmod tempor \
          incidunt ut labore et dolore magna aliqua."
    link=g.site.host_url
    html_body = HTML_email('with_button.j2',
                            header_image_url=g.site.get_email_header_url(),
                            primary_color=g.site.primary_color,
                            footer=g.site.get_email_footer(),
                            body=body,
                            link=link,
                            button_text=_("A button"))
    return {'html': html_body, 'text': f"{body}\n\n{link}"}

class Dispatcher(EmailServer):
    def __init__(self):
        self.site = Site.find()
        EmailServer.__init__(self, self.site)

    def create_HTML_body(self, template_file, **kwargs):
        kwargs['header_image_url'] = self.site.get_email_header_url()
        kwargs['primary_color'] = self.site.primary_color
        if not 'footer' in kwargs:
            kwargs['footer'] = self.site.get_email_footer()
        return HTML_email(template_file, **kwargs)

    def create_multipart_message(self, text_body, html_body):
        text_part = MIMEText(text_body, _subtype='plain', _charset='UTF-8')
        html_part = MIMEText(html_body, _subtype='html', _charset='UTF-8')
        message = MIMEMultipart("alternative")
        message.attach(text_part)
        message.attach(html_part)
        return message

    def send_test_email(self, recipient_email):
        body = _("Congratulations!")
        message = MIMEText(body, _subtype='plain', _charset='UTF-8')
        message['Subject'] = Header(_("MAIL test")).encode()
        message['To'] = recipient_email
        status = self.send_mail(message)
        return status

    def send_invitation(self, invite):
        link = invite.get_link()
        text_body = f"{invite.message}\n\n{link}"
        html_body = self.create_HTML_body('with_button.j2',
                                            body=invite.message,
                                            button_text=_("Join LiberaForms"),
                                            button_link=link)
        message = self.create_multipart_message(text_body, html_body)
        header = Header(_("Invitation to LiberaForms"))
        message['Subject'] = header.encode()
        message['To'] = invite.email
        status = self.send_mail(message)
        return status

    def send_account_recovery(self, user):
        link = f"{g.site.host_url}site/recover-password/{user.token['token']}"
        body = _("Please use this link to create a new password")
        footer = _("If you did not request this email you can ignore it")
        text_body = f"{body}\n\n{link}\n\n{footer}"
        html_body = self.create_HTML_body('with_button.j2',
                                            body=body,
                                            button_text=_("Recover your password"),
                                            button_link=link,
                                            footer=footer)
        message = self.create_multipart_message(text_body, html_body)
        header = Header(_("LiberaForms. Recover password"))
        message['Subject'] = header.encode()
        message['To'] = user.email
        status = self.send_mail(message)
        return status

    def send_email_address_confirmation(self, user, email_to_validate):
        link = f"{self.site.host_url}user/validate-email/{user.token['token']}"
        body = _("Use this link to validate your email")
        text_body = f"{body}\n\n{link}"
        html_body = self.create_HTML_body('with_button.j2',
                                            body=body,
                                            button_text=_("Validate email"),
                                            button_link=link)
        message = self.create_multipart_message(text_body, html_body)
        header = Header(_("LiberaForms. Change email"))
        message['Subject'] = header.encode()
        message['To'] = email_to_validate
        status = self.send_mail(message)
        return status

    def send_new_user_notification(self, user):
        admins = User.find_all( isAdmin=True,
                                notifyNewUser=True,
                                validatedEmail=True,
                                blocked=False)
        body = _("New user '%s' created at %s" % (  user.username,
                                                    self.site.siteName))
        message = MIMEText(body, _subtype='plain', _charset='UTF-8')
        message['Subject'] = Header(_("LiberaForms. New user notification")).encode()
        for admin in admins:
            message['To'] = admin.email
            thr = Thread(
                    target=self.send_mail_async,
                    args=[current_app._get_current_object(), message]
            )
            thr.start()

    def send_new_form_notification(self, form):
        admins = User.find_all( isAdmin=True,
                                notifyNewForm=True,
                                validatedEmail=True,
                                blocked=False)
        body = _("New form '%s' created at %s" % (form.slug, self.site.siteName))
        message = MIMEText(body, _subtype='plain', _charset='UTF-8')
        message['Subject'] = Header(_("LiberaForms. New form notification")).encode()
        for admin in admins:
            message['To'] = admin.email
            thr = Thread(
                    target=self.send_mail_async,
                    args=[current_app._get_current_object(), message]
            )
            thr.start()


    def send_new_answer_notification(self, emails, answer, slug):
        body = _("New form answer in %s at %s\n" % (slug, self.site.siteName))
        for data in answer:
            body = "%s\n%s: %s" % (body, data[0], data[1])
        body = "%s\n" % body
        subject = Header(_("LiberaForms. New form answer")).encode()
        message = MIMEText(body, _subtype='plain', _charset='UTF-8')
        message['Subject'] = subject
        for email in emails:
            message['To'] = email
            thr = Thread(
                    target=self.send_mail_async,
                    args=[current_app._get_current_object(), message]
            )
            thr.start()

    def send_answer_confirmation(self, msg_to, form):
        message = MIMEMultipart('alternative')
        # TODO: Also send a plain text email
        html_body=MIMEText(form.after_submit_text_html, _subtype='html', _charset='UTF-8')
        message.attach(html_body)
        message['Subject'] = Header(_("Confirmation message")).encode()
        message['To'] = msg_to
        state = self.send_mail(message)
        return state

    def send_expired_form_notification(self, emails, form):
        body = _("The form '%s' has expired at %s" % (form.slug, self.site.siteName))
        subject = Header(_("LiberaForms. A form has expired")).encode()
        message = MIMEText(body, _subtype='plain', _charset='UTF-8')
        message['Subject'] = subject
        for email in emails:
            message['To'] = email
            thr = Thread(
                    target=self.send_mail_async,
                    args=[current_app._get_current_object(), message]
            )
            thr.start()

    def send_branding_preview(self, email):
        body = branding_body_preview()
        message = self.create_multipart_message(body['text'], body['html'])
        header = Header(_("LiberaForms. Email brand preview"))
        message['Subject'] = header.encode()
        message['To'] = email
        status = self.send_mail(message)
        return status

    """
    def send_password_success(recipient_email):
        body = _("Password reset successfully")
        message = MIMEText(body, _subtype='plain', _charset='UTF-8')
        header = Header(_("LiberaForms. Password reset"))
        message['Subject'] = header.encode()
        message['To'] = recipient_email
        status = EmailServer().send_mail(message)
        return status
    """

    def publish_form(self, form, fediverse=True):
        text = "This is test 1"
        fedi_publisher = FediPublisher().publish(text)
        pass
