#!/bin/bash

set -e

SCRIPTS=$(pwd)/init
echo "Starting..."

# checks:
echo "Checking required env variables..."
python -u $SCRIPTS/check_env.py

if [ "$?" != 0 ]; then
    echo "Env variable check failed. exiting."
    exit 1
fi

echo "Awaiting db startup..."
python -u $SCRIPTS/await_db.py

if [ $? == 0 ]; then
    echo "Error! DB not available, exiting..."
    exit 2
fi

# application:
python -u $SCRIPTS/start_peon.py
echo "App terminated (code=$?)."
