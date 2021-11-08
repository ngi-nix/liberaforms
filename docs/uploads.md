# File uploads

You must create and enryption key first. See docs/INSTALL.md

## ENABLE_UPLOADS

When set to `True`, two types of file uploads are enabled.

* Media: Images can be uploaded by users and included in their forms' markdown Introduction text.
* Attachments: A new `file field` is available in the form editor. Files (attachments) can be uploaded by anonymous users with each form.

Extra Admin settings are enabled:

* Mimetypes. Define permited Attachment file types. (PDF, PNG, ODT by default)
* Enable `file field` on a per user basis.
* Enable `file field` by default.

## Uploads

Uploaded files are saved in the `./uploads` directory.

Remember to `chown -R <user>` the directory so that it can be written to.

> You should include the `./uploads` directory in your backups!

### DEFAULT_USER_UPLOADS_LIMIT

The sum of total media and attachments files.

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
