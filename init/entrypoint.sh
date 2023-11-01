#!/bin/bash

set -e

SCRIPTS="$(dirname -- "${BASH_SOURCE[0]}")"
echo "Starting..."

# checks:
echo "Checking required env variables..."
python -u $SCRIPTS/check_env.py

if [ "$?" != 0 ]; then
    echo "Env variable check failed. exiting."
    exit 1
fi

echo "Checking database availability..."
if [ "$DB_ENABLED" == "true" ]; then
    python -u $SCRIPTS/await_db.py
else
    echo "Database availability skipped. (DB_ENABLED != true)"
fi

if [ $? != 0 ]; then
    echo "Error! DB not available, exiting..."
    exit 2
fi

# application:
python -u /app/start.py
echo "App terminated (code=$?)."
