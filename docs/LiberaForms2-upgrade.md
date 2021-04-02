# LiberaForms2 upgrade

Use this documentation to upgrade from LiberaForms1 to LiberaForms2


```
mv config.cfg .env
```

Edit `.env` and add these lines

```
FLASK_ENV=production
FLASK_CONFIG=production
```

## Nginx

Nginx is much faster serving static files than flask.
We have added two new locations to take load off the LiberaForms app.

```
location /static/ {
    alias  /path/to/liberaforms/static;
}
location /favicon.png {
    alias  /path/to/liberaforms/instancesfiles/brand/favicon.png;
}

```
See `docs/nginx.example` for an example configuration.
