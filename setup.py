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

setup(
    name = "LiberaForms",
    version = "1.8.13",
    author = "LiberaForms team",
    author_email = "info@liberaforms.org",
    description = ("Form management software."),
    license = "AGPLv3",
    keywords = "forms privacy",
    url = "http://packages.python.org/an_example_pypi_project",
    packages=find_packages(),
    long_description=read('README.md'),
    include_package_data=True,
    install_requires= [

        "WTForms==2.2.1",
        "flask_mongoengine==0.9.5",
        "password_strength==0.0.3.post2",
        "Markdown==3.2.1",
        "validate_email==1.3",
        "passlib==1.7.2",
        "Unidecode==1.1.1",
        "Flask==1.1.1",
        "Flask_WTF==0.14.3",
        "mongoengine==0.19.1",
        "Flask_Babel==1.0.0",
        "unicodecsv==0.14.1",
        "beautifulsoup4==4.9.3",
        "flask_session==0.3.2",

    ],
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    entry_points={
        'console_scripts': [
            'liberaforms-migrate-db = liberaforms.scripts.migrate_db:migrate_db',
        ],
        'flask.commands': [
            'config_init = liberaforms.cli.custom_commands:config_init',
            'config_show = liberaforms.cli.custom_commands:config_show',
            'db_migrate = liberaforms.cli.custom_commands:db_migrate',
        ],
    },
)
