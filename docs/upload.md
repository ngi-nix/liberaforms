# File uploads

## ENABLE_UPLOADS

When set to `True` users can include a 'upload a file' field in their forms.

## MAX_FILE_UPLOAD_SIZE

The maximum size in Kbytes of the uploaded files

## ENABLE_REMOTE_STORAGE

When set to `False`, uploaded files are saved on your server's filesystem.

When `True` files are save on a Object Storage Server. LiberaForms uses the Minio client library which is uses the S3 protocol.

Minio server software is free software. You will need a server to use this option. You could install your own, or create an account on an available server open to registration.

In any case, you need to add these lines to your `.env` file

Where `FQDN` is the host name of the minio sever and, optionally, `:PORT` is the port.

```
MINIO_HOST = FQDN[:PORT]
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
```
