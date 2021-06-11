# File uploads

## ENABLE_UPLOADS

When set to `True` users can
* include a file attachment field in their forms. Attachments are saved as `./uploads/attachments/<form_id>/<random_string>.<answer_id>`
* upload images to include in the form's 'Introduction text'. Images are saved as `./uploads/media/<random_string>.<extension>`


## MAX_ATTACHMENT_SIZE

The maximum size in Kbytes of the uploaded files

## ENABLE_REMOTE_STORAGE

`False`: uploaded files are saved on your server's filesystem in the
directory `./uploads`

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

### Encryption

LiberaForms encrypts attachments before uploading them to the remote Minio server.

```
pip install "cryptography>=3.4.7,==3.*"
```

#### Create the keys

```
flask cryptokey create

olYyUwGTCxnx1BPn9AMsm8GoH9oc9AkH_HoMEW--g9Q=

```

Very Important! Save this key somewhere safe, and don't lose it.

Copy the generated key and save it in a file with a name you will recognize. Something like `my.domain.com.key`.

Now add the key you have generated to your `.env` file

```
CRYPTO_KEY=olYyUwGT--this-is-my-key--oH9oc9AkH_HoMEW--g9Q=
```

### Remote storage failure

If remote storage is configured and LiberaForms is unable to use the server (temporarily unavailable, network issues, etc), then:

* uploaded files are saved locally on the server at `./uploads`
* the problem is logged

# Nginx config

https://serverfault.com/questions/987061/nginx-proxying-s3-public-bucket-hosted-by-minio-service
