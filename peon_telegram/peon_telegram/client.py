
"""Telegram client."""

import logging

from .handlers import HANDLERS
from peon_common.utils import ENV_TOKEN_TELEGRAM, get_env_vars
from telegram import Update
from telegram.ext import ApplicationBuilder


logging.getLogger("httpx").setLevel(logging.WARNING)  # disable requests spam

class Peon():
    """Telegram Peon client."""

    ENV_VARS = get_env_vars()
    APPLICATION = None

    def __init__(self):
        pass

    def run(self):
        self.APPLICATION = ApplicationBuilder().token(
            self.ENV_VARS[ENV_TOKEN_TELEGRAM]).build()

        for handler in HANDLERS:
            self.APPLICATION.add_handler(handler)

        self.APPLICATION.run_polling(allowed_updates=Update.ALL_TYPES)
