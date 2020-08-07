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
        }

        self.client = discord.Client(**client_params)
        # await self.register_events()

        @self.client.event
        async def on_ready():
            print('Logged in as')
            print(self.client.user.name)
            print(self.client.user.id)
            print('------')

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
