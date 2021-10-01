# Install LiberaForms

Requires
* Python3.7 or greater.
* A PostgreSQL server


If you want to use Docker, please follow the instructions in `docs/docker.md`


Install development libraries to compile pip packages
```
apt-get install python3-dev
```

## Clone LiberaForms

You can install LiberaForms in the directory of your choice.

```
apt-get install git
git clone https://gitlab.com/liberaforms/liberaforms.git
cd liberaforms
```

## Create a Python venv

```
apt-get install python3-venv
python3 -m venv ./venv
```

### Install python packages
```
source ./venv/bin/activate
pip install --upgrade pip
pip install -r ./requirements.txt
```

## Configure

### Create and edit `.env`
```
cp dotenv.example .env
```

You can create a SECRET_KEY like this
```
openssl rand -base64 32
```

Add the database config.
```
DB_HOST=localhost
DB_NAME=liberaforms
DB_USER=liberaforms
DB_PASSWORD=a_secret_db_password
```

### Database

Create a user and database with the `.env` values

```
sudo su
su postgres -c "liberaforms/commands/postgres.sh create-db"
exit
```

#### Create tables

Upgrade the database to the latest version

```
flask db upgrade
```

See more db options here https://flask-migrate.readthedocs.io/en/latest/#api-reference


### Drop database

If you need to delete the database (and user)

```
sudo su
su postgres -c "liberaforms/commands/postgres.sh drop-db"
exit
```

## Encryption

LiberaForms encrypts passwords by default.

These other values are also encrypted:

* Form attachments when they are submitted
* Fediverse authentification

You need to create a key for those to work.

### Create the key

```
flask cryptokey create

olYyUwGT--example-key--c9AkH_HoMEWg9Q=

```

> Important. Save this key somewhere safe and do not lose it!

Copy the generated key and save it in a file with a name you will recognize.
Something like `my.domain.com.key`.

Now add the key you have generated to your `.env` file

```
CRYPTO_KEY=olYyUwGT--example-key--c9AkH_HoMEWg9Q=
```

Restart LiberaForms to take efect.

### Session data

```
SESSION_TYPE = "filesystem"
#SESSION_TYPE = "memcached"
```

If you use `filesystem` you must ensure the user running LiberaForms has write permissions
on the directory. For example

```
chown www-data ./liberaforms/flask_session
```

## Configure Gunicorn

Gunicorn serves LiberaForms.

This command suggests a configuration file path and it's content.

```
flask config hint gunicorn
```

Copy the content. Create the file `./gunicorn.py` and paste.


## Install Supervisor

Supervisor manages Gunicorn. It will start the process when the server boots.
```
sudo apt-get install supervisor
```

### Configure Supervisor

This command suggests a configuration file path and it's content.

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

# Backups

## Database

Create a directory for the backup and set permissions

```
mkdir /var/backups/liberaforms
chown postgres /var/backups/liberaforms/
```

Run this and check if a copy is dumped correctly.
```
su postgres -c "/usr/bin/pg_dump <db_name> > /var/backups/liberaforms/backup.sql"
```

Add a line to postgres user's crontab
```
crontab -u postgres -e
```
to run it every night..
```
30 3 * * * /usr/bin/pg_dump -U <db_name> > /var/backups/liberaforms/backup.sql"
```

Note: This overwrites the last copy. You might want to change that.

Don't forget to check that the cronjob is dumping the database correctly.

## Uploaded files

If you enabled `ENABLE_UPLOADS` in the `.env` file, LiberaForm will save
uploaded files in the `./uploads` directory, you should make copies of this directory.

## CRYPTO_KEY

Do not lose it!

# Debugging
You can check supervisor's log at `/var/log/supervisor/...`

You can also run LiberaForms in debug mode.
```
sudo supervisorctl stop liberaforms
FLASK_ENV=development flask run
```

# Configure nginx proxy
See `docs/nginx.example`


# Installation finished!

Stop the flask server if you still have it running in a terminal.

Start LiberaForms

```
supervisorctl start liberaforms
```

## Bootstrap the first admin user

## Setup SMTP


# Utilities

## Site config

By default new sites create public links like so

```
http://my.domain.com/xxxx
```

You can set the scheme and port

```
flask config set public-links -scheme=http -port=4000
```



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
