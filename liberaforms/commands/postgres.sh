#!/bin/bash

# This file is part of LiberaForms.
# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later

if [ -f .env ]
then
  export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
else
  echo "Cannot find .env file"
  exit 1
fi

if [[ "${1}" == "create-db" ]]
then
  psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'"
  psql -c "CREATE DATABASE $DB_NAME ENCODING 'UTF8' TEMPLATE template0"
  psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER"
  exit 0
fi

if [[ "${1}" == "drop-db" ]]
then
  psql -c "DROP DATABASE $DB_NAME"
  psql -c "DROP USER IF EXISTS $DB_USER"
  exit 0
fi
