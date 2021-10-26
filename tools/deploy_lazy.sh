#!/bin/bash

set -e
PROG="${0##*/}"

cd "$( dirname "$BASH_SOURCE" )"
cd ../

git reset --hard $(git rev-list --parents HEAD | egrep "^[a-f0-9]{40}$")
git pull

docker-compose build
docker-compose down
docker-compose up -d
