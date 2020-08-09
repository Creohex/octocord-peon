import sys
import time
import traceback

from peon.utils import Mongo


retry_limit = 15
retry_counter = 1
print("Waiting for db to come online... (%s retries)" % retry_limit)

while True:

    try:
        client = Mongo().client
        client.testDB.testColl.insert({"testkey": "testvalue"})
        client.drop_database("testDB")
        client.close()
        print("Successfully connected.")
        exit(0)
    except:
        print("(%s) Couldn't connect to db, retrying..." % retry_counter, flush=True)
        traceback.print_exc()

        retry_counter += 1
        if retry_counter > retry_limit:
            print("Exceded retry limit. Failed to connect to db.", flush=True)
            exit(1)

        time.sleep(2)
