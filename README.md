# LiberaForms

## *Provisional README under development!*

Create a form, choose a URL slug, and publish it!

Project page [https://liberaforms.org](https://liberaforms.org)

We are building this software with the hope it will be used by our neighbours, friends, and anyone else who feels GAFAM already has way to much data on **all** of us.


## Resources
Sharing resources makes things easier so LiberaForms has been built to share server infraestructure with others.

One installation, one database, one monitoring, and one backup system means less work for sysadmins too.

# Installation

For docker installation please see docker/

## Install mongodb
https://docs.mongodb.com/manual/tutorial/install-mongodb-on-debian/

## Install LiberaForms
Create a virtual environment some where on the filesystem where you have write permissons.

You can do this as root, but remember to `chown -R <username> ./liberaforms` when you finish.

### Get the source code

You can download a gzip'd tar file
```bash
wget https://gitlab.com/liberaforms/liberaforms/-/archive/main/liberaforms-main.tar.gz
mkdir liberaforms
tar zxvf liberaforms-main.tar.gz --strip-components=1 -C liberaforms
```
or clone the git repository
```bash
git clone https://gitlab.com/liberaforms/liberaforms.git liberaforms
or ..
git clone git@gitlab.com:liberaforms/liberaforms.git liberaforms
```
### Install the software
```bash
cd liberaforms
python3 -m venv ./venv
source ./venv/bin/activate
pip install -e ./
```

*Note: **All the following commands** that begin with `flask` require you to have activated the virtual environment.*
```bash
source ./venv/bin/activate
```
## Configure
Show the configuration and edit the `config.cfg` file as needed.
```bash
flask app_config_show
```

## Run/test LiberaForms on localhost
```bash
flask run
```
Browse `http://localhost:5000`

## Run in debug mode
```bash
FLASK_DEBUG=True flask run
```

# Production installation

*Note: These instructions are not necessary when installing with docker.*

After installing LiberaForms, and after creating and editing `config.cfg`
## Create the gunicorn config
```bash
flask gunicorn_config_init
```
You can always see your configuration with
```bash
flask gunicorn_config_show
```
Test the configuration with the command that is displayed.

### Install Supervisor to manage gunicorn
```bash
sudo apt-get install supervisor
```
You need to create a conf file for supervisor. Try
```bash
flask supervisor_config
```
Copy the output, create the supervisor conf file, and paste.

Restart supervisor to activate the new conf.
```bash
sudo systemctl restart supervisor
```
Supervisor commands you can use
```bash
sudo supervisorctl start|stop|restart|status LiberaForms
```

### Nginx or Apache or ..
1. Install a web server
2. Configure (letsencrypt) certificates for your domain
3. Create a host configuration for your LiberaForms domain. (see docs/nginx.example)


# Post installation
## Create the first user
If you installed locally, browse `http://localhost:5000/site/recover-password`

If you installed on a remote server, `https://domain.com/site/recover-password`

and enter your `ROOT_USER` email.

## SMTP
The first thing you should get working is the SMTP config. Browse the 'Config' page.

# Backups

Make sure you are dumping the database and saving off site.

## Database
Run this and check if a copy is dumped correctly.
```bash
/usr/bin/mongodump --db=liberaforms --out="/var/backups/"
```

Add a line to your crontab to run it every night.
```
30 3 * * * /usr/bin/mongodump --db=liberaforms --out="/var/backups/"
```
*Note: This overwrites the last copy. You might want to change that.*

## LiberaForms

These are some other files, not many, that do not change often. If you are hosting multiple domains, you will want to backup the 'branding' directory.

Run this command to show the directories and files you might backup.

```bash
flask backup_dirs_show
```

# Multisite
One server can serve multiple domains. An nginx proxy in front of LiberaForms routes the domains you choose to the gunicorn process.

1. Get your friend/tenant to point their subdomain to your server IP.
2. Configure nginx proxy to direct traffic to the running gunicorn process.
3. Go to your config page and send the person you know an Admin invitation for the new site.
4. Tell them to go to the configuration page and get the SMTP config working first.
