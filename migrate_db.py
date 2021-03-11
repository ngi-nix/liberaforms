"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from liberaforms import app
from liberaforms.models.site import Installation

def migrate_db():
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

if __name__ == '__main__':
    migrate_db()
