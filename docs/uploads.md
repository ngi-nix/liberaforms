# File uploads

## ENABLE_UPLOADS

When set to `True`, two types of file uploads are enabled.

* Media: Images can be uploaded by users and included in their forms' markdown Introduction text.
* Attachments: A new `file field` is available in the form editor. Files (attachments) can be uploaded by anonymous users with each form.

Extra Admin settings are enabled:

* Mimetypes. Define permited Attachment file types. (PDF, PNG, ODT by default)
* Enable `file field` on a per user basis.
* Enable `file field` by default.

## Storage

Uploaded files are saved in the `./uploads` directory.

Run this command to ensure the sub directories are created

```
flask storage create
```

You should include the `./uploads` directory in your backups!

### MAX_MEDIA_SIZE


### MAX_ATTACHMENT_SIZE

The maximum size in Kbytes of the uploaded files


## Encryption

LiberaForms encrypts form attachments when they are submitted.

### Create the key

```
flask cryptokey create

olYyUwGT--example-key--c9AkH_HoMEWg9Q=

```

Very Important! Save this key somewhere safe and don't lose it.

Copy the generated key and save it in a file with a name you will recognize. Something like `my.domain.com.key`.

Now add the key you have generated to your `.env` file

```
CRYPTO_KEY=olYyUwGT--example-key--c9AkH_HoMEWg9Q=
```


## ENABLE_REMOTE_STORAGE

`False`: uploaded files are saved on your server's filesystem under the
directory `./uploads`.

`True`: files are saved on an Object Storage Server. LiberaForms uses the Minio client library which uses the S3 protocol.
Minio server software is free software. You will need an account on a server to use this option.

### Configure remote storage

The minio package is not included in `./requirements.txt`, so install it now

```
pip install "minio>=7.0.3,==7.*"
```

Add these lines to your `.env` file where `FQDN` is the host name of the minio sever and optionally, `:PORT` is the port.

```
MINIO_URL = https://FQDN[:PORT]
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
```

Now you can create the remote buckets. LiberaForms uses two buckets:

* `my.domain.com.media`: Media files go here. Anonymous Internet users can download these files.
* `my.domain.com.attachments`: Documents attached to forms are stored here.

#### Create remote buckets

```
flask storage create --remote-buckets
```

### Remote storage failure

If remote storage is enabled and LiberaForms is unable to use the server (temporarily unavailable, network issues, etc), then:

* uploaded files are saved locally on the server at `./uploads`
* the problem is logged
