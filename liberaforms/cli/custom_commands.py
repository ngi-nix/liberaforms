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

import os, shutil, click
from liberaforms import app

def _create_branding_dir():
    branding_dir = os.path.join(app.instance_path, 'branding')
    if not os.path.isdir(branding_dir):
        os.makedirs(branding_dir, exist_ok=True)

@app.cli.command("config_init")
def config_init():
    """
    #print("sys.prefix: {}".format(sys.prefix))
    print("app.instance_path: {}".format(app.instance_path))
    print("realpath(__file__): {}".format(os.path.dirname(os.path.realpath(__file__))))
    print("app.root_path: {}".format(app.root_path))
    print("os.getcwd(): {}".format(os.getcwd()))
    """
    
    _create_branding_dir()
    conf_path = os.path.join(app.instance_path, 'config.cfg')
    if not os.path.isfile(conf_path):
        os.makedirs(app.instance_path, exist_ok=True)
        example_cfg = os.path.join(app.root_path, 'config.example.cfg')
        shutil.copyfile(example_cfg, conf_path)
        print("\nNew config file created: {}".format(conf_path))
        print("Don't forget to set a good SECRET_KEY !!")
    else:
        print("\nConfig file already exists: {}".format(conf_path))

@app.cli.command("config_show")
def config_show():
    conf_path = os.path.join(app.instance_path, 'config.cfg')
    
    if os.path.isfile(conf_path):
        print("Config file: {}\n".format(conf_path))
        with open(conf_path) as f:
            print(f.read())
    else:
        print("\nCound not find: {}\n".format(conf_path))
        print("Please run 'flask config_init'")


@app.cli.command("db_migrate")
def db_migrate():
    from liberaforms.models.site import Installation
    installation=Installation.get()
    print("Schema version is {}".format(installation.schemaVersion))
    if not installation.is_schema_up_to_date():
        updated=installation.update_schema()
        if updated:
            print("Migration completed OK")
            return True
        else:
            print("Error")
            print("Current database schema version is {} but should be {}".
                                                format( installation.schemaVersion,
                                                        app.config['SCHEMA_VERSION']))
            return False
    else:
        print("Database schema is already up to date")
        return True
