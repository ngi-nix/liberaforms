# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later

pythonpath = '/opt/LiberaForms'
command = './venv/bin/gunicorn'
#If your nginx proxy is on another machine, try 0.0.0.0 instead
bind = '127.0.0.1:5000'
workers = 3
user = 'www-data'
