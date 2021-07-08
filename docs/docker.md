# Single LiberaForms container installation

If you want to run multiple LiberaForms servers, please see the LiberaForms cluster project.

## Clone LiberaForms

```
apt-get install git
git clone https://gitlab.com/liberaforms/liberaforms.git
```

## Build the image

First create a docker image.
```
docker build -t liberaforms-app:$(cat VERSION.txt) .
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

### docker-compose

Create `docker-compose.yml` and edit as needed

```
cp docker-compose.yml.example docker-compose.yml
```

```
VERSION=$(cat VERSION.txt) docker-compose up -d
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

## Storage

See `./uploads.md` for some background.

To create storage for a container first you need a volume

Create a directory, for example

```
mkdir /opt/liberaforms_uploads
```
Make sure the write permission is set

Edit your `docker-compose.yml` and add the volume to the LiberaForms container config.
```
volumes:
  - /opt/liberaforms_uploads:/app/uploads
```

Remember to modify your `nginx` configuration to fit.

### Remote storage

The volume created in the previous step is neccesary. It is used if the Minio server becomes unavailable.

Now add these lines to your `docker-compose.yml`

```
MINIO_URL: ${MINIO_URL}
MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
```
And create the Minio buckets

```
flask storage create --remote-buckets --docker-container liberaforms-app
```


## Backups

### Database
```
docker exec <container> /usr/local/bin/pg_dump -U <db_user> <db_name> > backup.sql
```

### Uploads
