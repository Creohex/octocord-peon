"""Telegram client."""

import logging

from .handlers import HANDLERS
from peon_common.utils import ENV_TOKEN_TELEGRAM, get_env_vars
from telegram.ext import ApplicationBuilder


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


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

        self.APPLICATION.run_polling()
