from gngforms import app
from gngforms.models import Installation
from gngforms.utils import migrate


installation=Installation.get()

print("Schema version before upgrade is {}".format(installation.schemaVersion))
if not installation.isSchemaUpToDate():
    updated=installation.updateSchema()
    if updated:
        print("Updated database schema to version %s" % installation.schemaVersion)
        print("OK")
    else:
        print("Error")
        print("Current database schema version is {} but should be {}".format(installation.schemaVersion,
                                                                              app.config['SCHEMA_VERSION']))

else:
    print("Database schema is already up to date")
    print("OK")
