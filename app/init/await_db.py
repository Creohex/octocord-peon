import sys
import time
import traceback

from peon.db import check_connection


retry_limit = 10
retry_counter = 1
print("Waiting for db to come online... (%s retries)" % retry_limit)

while True:

    if check_connection():
        print("Database is available.")
        break
    else:
        print("(%s) Couldn't connect to db, retrying..." % retry_counter, flush=True)

        time.sleep(1)
