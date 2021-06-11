# Mutli tenant

> If you are using the **LiberaForms docker cluster**, please refer to that documentation instead.

A multi tenant setup enables you to serve various LiberaForms instances, each with their own domain name (FQDN).

* `.env`
* Port
* Database
* Uploads directory


## .env

Edit the `.env` of each LiberaForms' installation.

* Each tenant requires a unique database
* Add the tenant's domain name

```
DB_NAME=my_tenant_com
FQDN=my.tenant.com
```

## Port


# Uploads

## Nginx

Nginx serves media files.

```
# Remove this location
location /file/media/ {
    alias /path/to/liberaforms/uploads/media/;
}

# Add this location
location /file/media/ {
    alias /path/to/liberaforms/uploads/media/hosts/<FQDN>/;
}
```
