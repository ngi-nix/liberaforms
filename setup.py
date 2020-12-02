"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
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

import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name = "liberaforms",
    version = read('./liberaforms/VERSION').rstrip(),
    license = "AGPLv3",
    author = "LiberaForms team",
    author_email = "info@liberaforms.org",
    description = ("Form management software."),
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords = "forms privacy sovereignty",
    url = "https://liberaforms.org",
    
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Flask',
        'License :: OSI Approved :: GNU Affero General Public License v3 (AGPLv3)',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    project_urls={
        'Bug Reports': 'https://gitlab.com/liberaforms/liberaforms/-/issues',
        'Source': 'https://gitlab.com/liberaforms/liberaforms',
    },
    entry_points={
        'flask.commands': [
            'app_config_init = liberaforms.cli.custom_commands:app_config_init',
            'app_config_show = liberaforms.cli.custom_commands:app_config_show',
            'gunicorn_config_init = liberaforms.cli.custom_commands:gunicorn_config_init',
            'gunicorn_config_show = liberaforms.cli.custom_commands:gunicorn_config_show',
            'supervisor_config = liberaforms.cli.custom_commands:supervisor_config',
            'backup_dirs_show = liberaforms.cli.custom_commands:backup_dirs_show',
            'db_migrate = liberaforms.cli.custom_commands:db_migrate',
        ],
    },
)
