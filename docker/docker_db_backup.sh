#!/bin/bash

# usage
# bash backup_mongodb.sh --db_name liberaforms-dev --dest_dir /tmp

db_name=${db_name:-liberaforms} # defaut db_name: liberaforms
dest_dir=${dest_dir:-./}        # default dest_dir: ./

while [ $# -gt 0 ]; do
    if [[ $1 == *"--"* ]]; then
        param="${1/--/}"
        declare $param="$2"
        # echo $1 $2 // Optional to see the parameter:value result
    fi
    shift
done
dest=$dest_dir/$db_name-`date +%Y-%m-%d"_"%H_%M_%S`.mongodump

echo "Backup up" $db_name
docker exec liberaforms-mongodb_1 sh -c 'mongodump --db='"$db_name"' --archive' > $dest
