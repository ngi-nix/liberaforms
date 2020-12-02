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

from os import environ
from liberaforms import app

if app.config['SERVER_NAME']:
    host_port = app.config['SERVER_NAME'].split(':')
    host = host_port[0]
    try:
        port = host_port[1]
    except:
        port = 5000
else:
    host = "127.0.0.1"
    port = 5000

host = environ['FLASK_RUN_HOST'] if 'FLASK_RUN_HOST' in environ else host
port = int(environ['FLASK_RUN_PORT']) if 'FLASK_RUN_PORT' in environ else port
debug = False
if 'FLASK_DEBUG' in environ:
    if environ['FLASK_DEBUG'].lower() == "true":
        debug = True

#print("I am app.py")
if __name__ == "__main__":
    app.run(host=host, port=port, debug=debug)
