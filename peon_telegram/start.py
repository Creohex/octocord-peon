#!/usr/bin/env python3

from peon_common.db import initialize_db
from peon_telegram.client import Peon


def start():
    initialize_db()
    Peon().run()


if __name__ == "__main__":
    start()
