"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms.models.answer import AnswerAttachment
from liberaforms.models.media import Media
from liberaforms.utils.dispatcher.dispatcher import Dispatcher
from liberaforms.utils import utils

"""
Returns disk usage msg. Optionally sends email.
"""
def disk_usage(email, limit):
    total_media = Media.calc_total_size()
    total_attachments = AnswerAttachment.calc_total_size()
    total_usage = total_media + total_attachments
    msg = f"Total disk usage: {utils.human_readable_bytes(total_usage)}"
    if email:
        if limit:
            if total_usage > utils.string_to_bytes(limit):
                Dispatcher().send_message(email, "Disk usage alert", msg)
        else:
            Dispatcher().send_message(email, "Disk usage", msg)
    return msg
