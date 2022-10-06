#!/usr/bin/env python3

import time
from peon_common.db import check_connection


def await_db(retries=10):
    """Attempts to establish connection with database."""

    print("Waiting for db to come online... ({0} retries)".format(retries))

    for counter in range(1, retries + 1):
        if check_connection():
            print("Database is available.")
            exit(0)

        print("({0}) Couldn't connect to db, retrying...".format(counter),
                flush=True)
        time.sleep(1)
    else:
        print("Failed to connect to database!")
        exit(1)


if __name__ == "__main__":
    await_db(retries=20)
