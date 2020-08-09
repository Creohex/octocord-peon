#!/bin/bash

set -e
ROOT=$(pwd)
echo "Starting..."

echo "Checking required env variables..."
python $ROOT/init/check_env.py

if [ "$?" != 0 ]; then
    echo "Env variable check failed. exiting."; exit 1
fi

echo "Awaiting db startup..."
python $ROOT/init/await_db.py

if [ $? == "1" ]; then
    echo "Error! DB not available."
    exit 1
fi

python $ROOT/init/start_peon.py

echo "App terminated (code=$?)."
