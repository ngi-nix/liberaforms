# Install LiberaForms

Requires python3.7 or greater.

If you want to use Docker, please follow the instructions in `docs/docker.md`

## Clone LiberaForms

```
apt-get install git
git clone https://gitlab.com/liberaforms/liberaforms.git
```

## Create a Python venv

```
apt-get install python3-venv
python3 -m venv ./venv
```

### Install python packages
```
source ./venv/bin/activate
pip install -r ./requirements.txt
```

## Configure

#### Filesystem
Create this directory. session data will be saved there.
```
mkdir ./liberaforms/flask_session
chown www-data ./liberaforms/flask_session
```

#### Memory
If you prefer to use memcached, you need to do this.
```
apt-get install memcached
source ./liberaforms/venv/bin/activate
```

### Create and edit `.env`
```
cp dotenv.example .env
```

You can create a SECRET_KEY like this
```
openssl rand -base64 32
```

### File permissions


Admins can upload a logo. You need to give the system user who runs LiberaForms write permission
```
chown -R www-data ./liberaforms/liberaforms/static/images
```

## Database

Install PostgreSQL

### Create the empty database

This will use the DB values in your `.env` file
```
flask database create
```

### Initialize schema versioning

```
flask database init
```

### Create tables

Update the database to the latest version

```
flask database update
```

### Drop database

If you need to delete the database

```
flask database drop
```

### Database backup

Run this and check if a copy is dumped correctly.
```
/usr/bin/pg_dump -U <db_user> <db_name> > backup.sql
```

Add a line to your crontab to run it every night.
```
30 3 * * * /usr/bin/pg_dump -U <db_user> <db_name> > backup.sql
```
Note: This overwrites the last copy. You might want to change that.

Don't forget to check that the cronjob is dumping the database correctly.

## Test your installation

```
flask run
ctrl-c
```

## Configure Gunicorn

Gunicorn serves LiberaForms.

This command will suggest a configuration file path and it's content. It will also output a command to test the configuration.
```
flask config hint gunicorn
```
Copy the content. Create the `gunicorn.py` file and paste.

## Install Supervisor

Supervisor manages Gunicorn. It will start the process when the server boots.
```
sudo apt-get install supervisor
```
### Configure Supervisor

This command will suggest a configuration file path and it's content.
```
flask config hint supervisor
```
Copy the content. Create the `liberaforms.conf` file and paste.

Restart supervisor and check if LiberaForms is running.
```
sudo systemctl restart supervisor
sudo supervisorctl status liberaforms
```
Other supervisor commands
```
sudo supervisorctl start liberaforms
sudo supervisorctl stop liberaforms
```


## Debugging
You can check supervisor's log at `/var/log/supervisor/...`

You can also run LiberaForms in debug mode.
```
sudo supervisorctl stop liberaforms
FLASK_ENV=development flask run
```

## Configure nginx proxy
See `docs/nginx.example`


# Utilities

## Users

You can create a user when needed.

Note that users created via the command line will have validated_email set to True

```
flask user create -admin <username> <email> <password>
```

Disable and enable users.

```
flask user disable <username>
flask user enable <username>
```
