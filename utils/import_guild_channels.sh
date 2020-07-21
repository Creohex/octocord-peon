#!/bin/bash

set -e
PROG="${0##*/}"

message() {
	printf '%s\n' "$PROG: $*" >&2
}

fatal() {
	message "$@"
	exit 1
}

get_uuid() {
    printf $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1) | cut -c1-5 | tr '[:upper:]' '[:lower:]'
}

[ $# -eq 2 ] ||
	fatal "Usage: $PROG BOT_TOKEN GUILD_ID"

TOKEN="$1" && shift
GUILD_NAME="$1" && shift

UUID=$(get_uuid)
EXPORTER="tyrrrz/discordchatexporter"
FOLDER="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )/exports/$UUID"

if [ -d "$FOLDER" ]; then
  rm -rf $FOLDER
fi

mkdir -p $FOLDER
echo "Output folder: $FOLDER"
echo "Name used for containers: $UUID"

# pull exporter image
echo "Pulling exporter image..."
docker pull $EXPORTER > /dev/null

# export chats
docker run $EXPORTER channels -t $TOKEN -b -g $GUILD_NAME | \
    egrep -o '^[0-9]+' | \
    while read CHANNEL_ID;
    do
        docker run --name $UUID $EXPORTER export -t $TOKEN -b -c $CHANNEL_ID -o "exp" -f Json
        docker cp $UUID:app/out/exp $FOLDER/$CHANNEL_ID
        docker rm $UUID > /dev/null
        mv "$(find $FOLDER/$CHANNEL_ID/ -mindepth 1 -print -quit)" $FOLDER/$CHANNEL_ID.json
        rm -rf $FOLDER/$CHANNEL_ID/
    done

echo "done!"
