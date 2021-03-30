import os
from liberaforms import create_app, db
from flask_migrate import Migrate
#from commands import register_commands

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

#migrate = Migrate(app, db)
#register_commands(app)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)
