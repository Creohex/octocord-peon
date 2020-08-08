import binascii
import json
import os
import random
import re
import requests
import time
import urllib.parse
import traceback

import discord
import pymysql

import peon.utils as utils

from peon.commands import commands, mention_handlers
from peon.utils import (
    ENV_TOKEN,
    ENV_RAPIDAPI_TOKEN,
)


class Peon():
    """Peon."""

    def __init__(self):
        self.env_vars = utils.get_env_vars()

    def run(self):
        """Run peon."""

        client_params = {
            "max_messages": 3000,
            "activity": discord.Game("work work"),
            "heartbeat_timeout": 30,
        }

        self.client = discord.Client(**client_params)

        @self.client.event
        async def on_ready():
            print("Logged in as\n{0}\n{1}\n------".format(
                self.client.user.name, self.client.user.id))

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return

            # handle commands
            for cmd in commands:
                if await cmd.execute(message):
                    return

            # handle mentions
            for handler in mention_handlers:
                if await handler(message):
                    return

        self.client.run(self.env_vars[ENV_TOKEN])
