# LiberaForms2 upgrade

> Use this documentation to upgrade from LiberaForms1 to LiberaForms2

## Migrate the database

First, follow and complete the instructions at https://gitlab.com/liberaforms/mongo2postgres

## Download LiberaForms2

After migrating the database ...
```
git clone ..
```

## Configuration

```
mv config.cfg .env
```

Edit `.env` and add these lines

```
# See docs/upload.md
ENABLE_UPLOADS = False
# 1024 * 500 = 512000 = 500 KiB
MAX_MEDIA_SIZE=512000
# 1024 * 1024 * 1.5 = 1572864 = 1.5 MiB
MAX_ATTACHMENT_SIZE=1572864
ENABLE_REMOTE_STORAGE=False

# Logging [watched|stream]
LOG_TYPE=watched
LOG_DIR=./logs

FLASK_ENV=production
FLASK_CONFIG=production
```
See a complete example at `./dotenv.example`


## Nginx

Nginx is much faster serving static files than Flask.
We have added new locations to take load off the LiberaForms app.

```
location /static/ {
    alias  /path/to/liberaforms/static;
}
location /favicon.ico {
    alias /path/to/liberaforms/uploads/media/brand/favicon.ico;
}
location /brand/emailheader.png {
    alias  /path/to/liberaforms/uploads/media/emailheader.png;
}
location /file/media/ {
    alias /path/to/liberaforms/uploads/media/;
}
```
See `docs/nginx.example` for a complete example configuration.


## Site icon

The favicon file type has been changed to `ico`. You need to upload your site icon (`png` or `jpg`) again. It will be converted to `ico` for you.
