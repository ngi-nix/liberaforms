
# Install LiberaForms

Requires python3.7 or greater

## Install PostgreSQL




## Clone LiberaForms


```
apt-get install git
git clone https://gitlab.com/liberaforms/liberaforms.git /opt/LiberaForms
```

## Create a python3 venv

If you have Python3 on your host
```
apt-get install python3-venv
python3 -m venv /opt/LiberaForms/venv
```
Or if you have old python2 on your host
```
apt-get install virtualenv
virtualenv /opt/LiberaForms/venv --python=python3
```

### Install python packages
```
source ./venv/bin/activate
pip install --upgrade setuptools
pip install wheel
pip install -r ./requirements.txt
pip install gunicorn
```

## Configure

#### Filesystem
Create this directory. session data will be saved there.
```
mkdir /opt/LiberaForms/liberaforms/flask_session
chown www-data /opt/LiberaForms/liberaforms/flask_session
```

#### Memory
If you prefer to use memcached, you need to do this.
```
apt-get install memcached
source /opt/LiberaForms/venv/bin/activate
pip install pylibmc
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
chown -R www-data /opt/LiberaForms/liberaforms/static/images
```

## Database
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
/usr/bin/mongodump --db=LiberaForms --out="/var/backups/"
```

Add a line to your crontab to run it every night.
```
30 3 * * * /usr/bin/mongodump --db=LiberaForms --out="/var/backups/"
```
Note: This overwrites the last copy. You might want to change that.


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
