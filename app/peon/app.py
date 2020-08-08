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

from peon import commands
from peon.commands import CommandSet, Command, MentionHandler
from peon.utils import (
    ENV_TOKEN,
    ENV_RAPIDAPI_TOKEN,
)


class Peon():
    """Peon."""

    def __init__(self):
        self.env_vars = utils.get_env_vars()
        self.command_set = commands.CommandSet()
        self.command_set.register([
            Command("peon", commands.cmd_peon),
            Command("test", commands.cmd_test),
            Command("tr", commands.cmd_tr),
            Command("roll", commands.cmd_roll),
            Command("starify", commands.cmd_starify),
            Command("slot", commands.cmd_slot),
            Command("wiki", commands.cmd_wiki),
            Command("urban", commands.cmd_urban),
            Command("stats", commands.cmd_stats),
            MentionHandler(commands.handle_simple_replies),
            MentionHandler(commands.handle_emergency_party_mention),
        ])

    def run(self):
        """Run peon."""

        client_params = {
            "max_messages": 3000,
            "activity": discord.Game(name="work work"),
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

            await self.command_set.execute(message)

        self.client.run(self.env_vars[ENV_TOKEN])
