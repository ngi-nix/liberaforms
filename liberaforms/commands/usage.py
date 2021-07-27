"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os, shutil
import click
import signal, subprocess
from flask import current_app
from flask.cli import AppGroup
from liberaforms.models.answer import Answer
from liberaforms.utils.storage.remote import RemoteStorage


usage_cli = AppGroup('usage')

def run_subprocess(cmdline):
    try:
        p = subprocess.Popen(cmdline)
        p.wait()
    except KeyboardInterrupt:
        p.send_signal(signal.SIGINT)
        p.wait()


@usage_cli.command()
@click.option('--user_id', 'user_id',
                help="User id"
              )
def answers(user_id):
    answer_cnt = Answer.find_all(author_id=user_id).count()
    # Do something
    click.echo(f"{answer_cnt} answers")
    #return answer_cnt
