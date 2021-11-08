# File uploads

> Uploads are encrypted with the `CRYPTO_KEY` value defined in the `.env` file.
See docs/INSTALL.md first

Check the total uploads. Optionally send the result by email
```
flask storage usage --email=me@my.domain.com
```
Only send an email if total uploads is greater than `alert` in KB, MB, or GB.

```
flask storage usage --email=me@my.domain.com --alert="2.5 GB"
```
You could use this as a cronjob.

```
/path/to/liberaforms/venv/bin/flask storage usage --email=me@my.domain.com --alert="2.5 GB"
```

Using a docker container
```
docker exec <container_name> flask storage usage --email=me@my.domain.com --alert="2.5 GB"
```


## ENABLE_UPLOADS

When set to `True`, two types of file uploads are enabled.

* Media: Images can be uploaded by users and included in their forms' markdown Introduction text.
* Attachments: A new `file field` is available in the form editor. Files (attachments) can be uploaded by anonymous users with each form.

Extra Admin options are enabled:

* Mimetypes. Define permited Form attachment file types. (PDF, PNG, ODT by default)
* Enable uploads for new users by default.
* Enable uploads on a per user basis.
* Define uploads limit on a per user basis.


## Uploads

Uploaded files are saved in the `./uploads` directory.

Remember to `chown -R <user>` the directory so that it can be written to.

> You should include the `./uploads` directory in your backups!

### DEFAULT_USER_UPLOADS_LIMIT

Users' default limit. The sum of total media and attachments files.

### MAX_MEDIA_SIZE

The maximum size in bytes of the files that can be uploaded by form editors.


### MAX_ATTACHMENT_SIZE

The maximum size in bytes of the files that can be attached to forms.


## ENABLE_REMOTE_STORAGE

`False`: uploaded files are saved on your server's filesystem under the
directory `./uploads`.

`True`: files are saved on an Object Storage Server. LiberaForms uses the Minio client library which uses the S3 protocol.
Minio server software is free software. You will need an account on a server to use this option.

### Configure remote storage


Add these lines to your `.env` file where `FQDN` is the host name of the minio sever and optionally, `:PORT` is the port.

```
MINIO_URL = https://FQDN[:PORT]
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
```

Create the remote buckets. LiberaForms uses two buckets:

* `my.domain.com.media`: Media files go here. Anonymous Internet users can download these files.
* `my.domain.com.attachments`: Documents attached to forms are stored here.

#### Create remote buckets

```
flask storage create --remote-buckets
```

### Remote storage failure

If remote storage is enabled but becomes temporarily unavailable (network issues, maintainence downtime, etc), LiberaForms will:

* save the attachments locally on the server in `./uploads/attachments`
* log the problem
