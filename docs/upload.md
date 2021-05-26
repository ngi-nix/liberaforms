# File uploads

## ENABLE_UPLOADS

When set to `True` users can include a 'upload a file' field in their forms.

Form attachments are saved like this: `./answers/<form_id>/<random_string>.<answer_id>`

## MAX_FILE_UPLOAD_SIZE

The maximum size in Kbytes of the uploaded files

## ENABLE_REMOTE_STORAGE

`False`: uploaded files are saved on your server's filesystem in the
directory `instancefiles/uploads`

`True`: files are saved on an Object Storage Server. LiberaForms uses the Minio client library which uses the S3 protocol.
Minio server software is free software. You will need an account on a server to use this option.

### Configure remote storage

The minio package is not included in `./requirements.txt`, so install it now

```
pip install minio
```

Add these lines to your `.env` file where `FQDN` is the host name of the minio sever and, optionally, `:PORT` is the port.

```
MINIO_HOST = FQDN[:PORT]
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
```

### Remote storage failure

If remote storage is configured and LiberaForms is unable to use the server (temporarily unavailable, network issues, etc), then:

* uploaded files are saved to `instancefiles/uploads`
* the problem is logged
