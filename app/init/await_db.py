import sys
import time
import traceback

from peon.db import check_connection


def await_db():
    retry_limit = 10
    retry_counter = 1
    print("Waiting for db to come online... (%s retries)" % retry_limit)

    while True:

        if check_connection():
            print("Database is available.")
            break
        else:
            if retry_counter >= retry_limit:
                raise Exception("DB not available!")

            print("(%s) Couldn't connect to db, retrying..." % retry_counter, flush=True)
            retry_counter += 1
            time.sleep(1)


if __name__ == "__main__":
    await_db()
