from gngforms import app
from gngforms.models import Installation
from gngforms.utils import migrate


installation=Installation.get()

print("Schema version is {}".format(installation.schemaVersion))
if not installation.isSchemaUpToDate():
    updated=installation.updateSchema()
    if updated:
        print("Migration completed OK")
    else:
        print("Error")
        print("Current database schema version is {} but should be {}".format(installation.schemaVersion,
                                                                              app.config['SCHEMA_VERSION']))

else:
    print("Database schema is already up to date")
    print("OK")
