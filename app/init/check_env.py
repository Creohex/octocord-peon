#!/usr/bin/env python3

from peon.utils import get_env_vars


if __name__ == "__main__":
    print("Verifying environment variables...")
    get_env_vars()
    print("Environment variables verified.")
