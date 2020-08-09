import re

import discord

from peon import commands, CommandSet, Command, MentionHandler
from peon.utils import (
    get_env_vars,
    ENV_TOKEN,
    ENV_RAPIDAPI_TOKEN,
)


class Peon():
    """Peon."""

    @property
    def client(self):
        """Discord client property representing Peon."""

        return self._client

    def __init__(self):
        self._client = None
        self.env_vars = get_env_vars()
        self.command_set = CommandSet(self)
        self.command_set.register([
            Command("peon", commands.cmd_peon, description="show bot stats"),
            Command("test", commands.cmd_test),
            Command("tr", commands.cmd_tr,
                    description="translate text (langs - en, et, ru, be, ...)",
                    examples=["{0} bla", "{0}<to_lang> bla",
                              "{0}<from_lang><to_lang> bla"]),
            Command("roll", commands.cmd_roll,
                    description="roll dice",
                    examples=["{0} d4", "{0} 2d8", "{0} 100",
                              "{0} 42-59", "{0} L8", "{0} 2d5+100+4d4"]),
            Command("starify", commands.cmd_starify,
                    description="write mystical stuff on night sky",
                    examples=["{0} each minute a minute passes"]),
            Command("slot", commands.cmd_slot, description="test your luck"),
            Command("wiki", commands.cmd_wiki,
                    description="query wiki", examples=["{0} nuclear fission"]),
            Command("urban", commands.cmd_urban,
                    description="query urban dictionary",
                    examples=["{0} lollygagging"]),
            Command("stats", commands.cmd_stats, description="print various peon stats"),
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

        self._client = discord.Client(**client_params)

        @self.client.event
        async def on_ready():
            print("Logged in as\n{0}\n{1}\n------".format(
                self._client.user.name, self.client.user.id))

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return

            await self.command_set.execute(message)

        self._client.run(self.env_vars[ENV_TOKEN])
