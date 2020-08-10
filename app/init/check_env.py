import importlib
import sys
import time

from peon.utils import get_env_vars


def verify_env():
    """Verify existing environment variables."""

    print("Verifying environment variables...")
    get_env_vars()


if __name__ == "__main__":
    verify_env()
