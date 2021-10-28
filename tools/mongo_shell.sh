#!/bin/bash

set -e
PROG="${0##*/}"

cd "$( dirname "$BASH_SOURCE" )"
cd ../

source .db.env

SHELL_PKG="mongodb-org-shell"
PACKAGE=$(yum list installed | grep mongodb-org-shell)

if [[ -z $PACKAGE ]]
then
    echo "$SHELL_PKG not found, installing..."
    echo "[mongodb-org-5.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/5.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-5.0.asc" \
    | sudo tee /etc/yum.repos.d/mongodb-org-5.0.repo
    yum install -y $SHELL_PKG
fi

mongo \
    --host localhost \
    --port $MONGO_PORT \
    -u $MONGO_INITDB_ROOT_USERNAME \
    -p $MONGO_INITDB_ROOT_PASSWORD
