"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import g, current_app
from liberaforms.models.formuser import FormUser
from liberaforms.utils.dispatcher.dispatcher import Dispatcher


"""
Expires the form and sends email notification
"""
def expire_form(form, expired=True):
    form.expired=expired
    form.save()
    if form.expired == True:
        emails=[]
        for form_user in FormUser.find_all(form_id=form.id):
            if form_user.user.enabled and form_user.notifications["expiredForm"]:
                # don't send an email to the current_user
                if g.current_user and g.current_user == form_user.user:
                    continue
                emails.append(form_user.user.email)
        if emails:
            try:
                Dispatcher().send_expired_form_notification(emails, form)
            except Exception as error:
                current_app.logger.error(error)
