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

The configuration has changed. The file is now called `.env`

```
cp dotenv.example .env
```

Edit `.env` and adjust

The `DB_USER` and `DB_PASSWORD` are the values you used during the mongo - postgres migration

## Nginx

Nginx is much faster serving static files than Flask.
We have added new locations to take load off the LiberaForms app.

See `docs/nginx.example` and adjust your nginx config.


## Caveats

The favicon file type has been changed to `ico`. You need to upload your site icon (`png` or `jpg`) again. It will be converted to `ico` for you.
