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
from liberaforms.config import ENV_VARIABLES

def _create_branding_dir():
    branding_dir = os.path.join(app.instance_path, 'branding')
    if not os.path.isdir(branding_dir):
        os.makedirs(branding_dir, exist_ok=True)

@app.cli.command("app_config_init")
def app_config_init():
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
        print("Don't forget to set a good SECRET_KEY !! (try 'openssl rand -base64 32')")
    else:
        print("\nConfig file already exists: {}".format(conf_path))

@app.cli.command("app_config_show")
def app_config_show():
    conf_path = os.path.join(app.instance_path, 'config.cfg')
    if os.path.isfile(conf_path):
        from configparser import ConfigParser
        parser = ConfigParser()
        with open(conf_path) as stream:
            parser.read_string("[top]\n" + stream.read())
        print("Config file: {}\n".format(conf_path))
        for key, value in parser.items('top'):
            print("{} = {}".format(key.upper(), value))
    env_vars=""
    for variable in ENV_VARIABLES:
        if variable in os.environ:
            env_vars=env_vars+"{} = {}\n".format(variable, os.environ[variable])
    if env_vars:
        print("\nEnvironment variables override config.cfg")
        print(env_vars)
    
@app.cli.command("gunicorn_config_init")
def gunicorn_config_init():
    gunicorn_config_path = os.path.join(app.instance_path, 'gunicorn.py')
    if os.path.isfile(gunicorn_config_path):
        print("\ngunicorn.py already exists: {}".format(gunicorn_config_path))
    else:
        from jinja2 import Environment, FileSystemLoader
        j2_env = Environment(loader = FileSystemLoader(os.path.join(app.root_path, 'data')))
        template = j2_env.get_template('gunicorn.jinja2')
        gunicorn_config = template.render({
                                'pythonpath': app.root_path,
                                'gunicorn_bin': '{}/bin/gunicorn'.format(os.environ['VIRTUAL_ENV']),
                                'username': os.environ.get('USER')
                                })
        gunicorn_config = "{}{}".format(gunicorn_config, os.linesep)
        new_config_file = open(gunicorn_config_path, 'w')
        new_config_file.write(gunicorn_config)
        new_config_file.close()
        print("\nNew gunicorn.py created: {}".format(gunicorn_config_path))
    print("Edit as needed. Ensure 'user' is set to the user who will run gunicorn.")
    print("Test config with 'gunicorn -c {} liberaforms:app'".format(gunicorn_config_path))

@app.cli.command("gunicorn_config_show")
def gunicorn_config_show():
    gunicorn_config_path = os.path.join(app.instance_path, 'gunicorn.py')
    if os.path.isfile(gunicorn_config_path):
        print("gunicorn.py: {}\n".format(gunicorn_config_path))
        with open(gunicorn_config_path) as f:
            print(f.read())
        print("Test config with 'gunicorn -c {} liberaforms:app'".format(gunicorn_config_path))
    else:
        print("\nCound not find: {}".format(gunicorn_config_path))
        print("Please run 'flask gunicorn_config_init'")

@app.cli.command("supervisor_config")
def supervisor_config():
    from jinja2 import Environment, FileSystemLoader
    j2_env = Environment(loader = FileSystemLoader(os.path.join(app.root_path, 'data')))
    template = j2_env.get_template('supervisor.jinja2')
    gunicorn_py = os.path.join(app.instance_path, 'gunicorn.py')
    supervisor_config = template.render({
                            'pythonpath': app.root_path,
                            'gunicorn_bin': '{}/bin/gunicorn'.format(os.environ['VIRTUAL_ENV']),
                            'gunicorn_py': gunicorn_py,
                            'username': os.environ.get('USER')
                            })
    print("Suggested supervisor config for /etc/supervisor/conf.d/LiberaForms.conf\n")
    print("{}\n".format(supervisor_config))

@app.cli.command("backup_dirs_show")
def backup_dirs_show():
    print("#\n# Remember: The most important thing to backup is your database!")
    print("# These _other_ files do not change often.\n#")
    print("# Your config")
    print(os.path.join(app.instance_path, 'config.cfg'))
    print(os.path.join(app.instance_path, 'gunicorn.py'))
    print("\n# Logos and favicons")
    print(os.path.join(app.instance_path, 'branding'))

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
