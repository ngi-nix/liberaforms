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

#import sys
import os, shutil
from liberaforms import app

def init_config():

    #print("sys.prefix: {}".format(sys.prefix))
    print("app.instance_path: {}".format(app.instance_path))
    print("realpath(__file__): {}".format(os.path.dirname(os.path.realpath(__file__))))
    print("app.root_path: {}".format(app.root_path))
    print("os.getcwd(): {}".format(os.getcwd()))
    
    conf_path = os.path.join(app.instance_path, 'config.cfg')
    if not os.path.isfile(conf_path):
        os.makedirs(app.instance_path, exist_ok=True)
        example_cfg = os.path.join(app.root_path, 'config.example.cfg')
        shutil.copyfile(example_cfg, conf_path)
        print("\nPlease edit new config file: {}".format(conf_path))
    else:
        print("\nConfig file already exists: {}".format(conf_path))
