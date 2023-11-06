#!/usr/bin/env python3

import logging
from peon_common.db import initialize_db
from peon_telegram.client import Peon

# NOTE: disable requests spam
logging.getLogger('httpx').setLevel(logging.WARNING)


def start():
    initialize_db()
    Peon().run()


if __name__ == "__main__":
    start()
