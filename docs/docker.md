# Docker

If you only want to run one LiberaForms server with Docker, this documentation is for you!

If you want to run multiple LiberaForms servers, please see the LiberaForms cluster project.

## Clone LiberaForms

```
apt-get install git
git clone https://gitlab.com/liberaforms/liberaforms.git
```

## Build the image

First create a docker image.
```
docker build -t liberaforms:latest .
```

## Compose

The `docker-compose.yml` will instantiate two containers: PostgreSQL and LiberaForms.
It will not setup a webserver, you will have to do that.

### Edit `.env`

The Postgres container requires two extra environment variables.

```
POSTGRES_ROOT_USER=
POSTGRES_ROOT_PASSWORD=

DB_HOST=liberaforms-db
```

Note that the name of the postgresql container will be set to `DB_HOST`

### Instantiate the containers

```
docker-compose up -d
```

## Create the database

```
flask database create --docker-container liberaforms-db
```

### Initialize schema versioning

```
flask database init --docker-container liberaforms-app
```

### Create tables

Update the database to the latest version

```
flask database update --docker-container liberaforms-app
```

### Drop database

If you need to delete the database

```
flask database drop --docker-container liberaforms-db
```

## backups

```
docker exec <container> /usr/local/bin/pg_dump -U <db_user> <db_name> > backup.sql
```
