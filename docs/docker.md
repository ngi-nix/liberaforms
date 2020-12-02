# Some docker notes 


## Developer mode

### From git repository
```bash
git clone git@gitlab.com:liberaforms/liberaforms.git liberaforms
or ..
git clone https://gitlab.com/liberaforms/liberaforms.git liberaforms

cd liberaforms
```

### From source
Download liberaforms src tgz
*Where <version> is the version you want to use*
```bash
wget https://pkg.liberaforms.org/liberaforms/liberaforms-<version>.tar.gz
tar zxvf liberaforms-<version>.tar.gz
cd liberaforms-<version>
```

And build
```bash
docker build -t liberaforms .
```

## Run container in development mode
```bash
cd liberaforms-<version>
docker run \
 --publish 5000:5000 \
 -v$PWD/liberaforms:/app/liberaforms \
 --rm=true \
 -e FLASK_DEBUG=True \
 -e FLASK_RUN_HOST=0.0.0.0 \
 -e MONGODB_HOST=127.0.0.1 \
 -e MONGODB_PORT=2701 \
 -e MONGODB_DB=liberaforms \
 liberaforms:latest

```

# Other
## Run container
```bash
docker run --publish 5000:5000 --rm liberaforms:latest
docker run --publish 5000:5000 --rm --detach liberaforms:latest
```
