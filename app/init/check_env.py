import importlib
import sys
import time

from peon.utils import get_env_vars


def verify_env():
    """Verify existing environment variables."""

    print("Attempting to get environment variables...")
    get_env_vars()
    print("Success!")


if __name__ == "__main__":
    verify_env()
