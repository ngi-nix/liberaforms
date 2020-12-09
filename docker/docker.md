# Docker installation 

You need docker and docker-compose installed first.

## Get the source code

You can download a gzip'd tar file
```bash
wget https://gitlab.com/liberaforms/liberaforms/-/archive/main/liberaforms-main.tar.gz
mkdir liberaforms
tar zxvf liberaforms-main.tar.gz --strip-components=1 -C liberaforms
```
or clone the git repository
```bash
git clone https://gitlab.com/liberaforms/liberaforms.git liberaforms
or ..
git clone git@gitlab.com:liberaforms/liberaforms.git liberaforms
```

## Build the liberaforms image and start the containers
```bash
cd liberaforms/docker/dev/
docker-compose -p liberaforms up -d
```
Browse `http://localhost:5000`

See README.md 'Post installation' notes

## Run in debug mode
*See comments in `docker-compose.yml`*


# mongodb backup
```
bash backup_mongodb.sh --db_name liberaforms --dest_dir /tmp
```
Recover
```
docker exec -i liberaforms_mongodb_1 sh -c 'mongorestore --archive' < /tmp/xxxx.mongodump
```

# Other notes to be organized ...

Build
```bash
docker build -t liberaforms .
```

## Run container
```bash
docker run --publish 5000:5000 --rm liberaforms:latest
docker run --publish 5000:5000 --rm --detach liberaforms:latest
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
