import re

from datetime import datetime

import discord

from peon import commands, CommandSet, Command, MentionHandler
from peon.utils import (
    get_env_vars,
    get_file,
    ENV_TOKEN,
    ENV_RAPIDAPI_TOKEN,
)


class Peon():
    """Peon."""

    NAME = "Peon"
    GAME_NAME = "work work"
    AVATAR = get_file("{0}.png".format(NAME))
    __INSTANCE = None

    @property
    def client(self):
        """Discord client property representing Peon."""

        return self._client

    def __new__(cls):
        """Ensure singleton."""

        if Peon.__INSTANCE is None:
            Peon.__INSTANCE = super(Peon, cls).__new__(cls)

        return Peon.__INSTANCE

    def __init__(self):
        self._client = None
        self.env_vars = get_env_vars()
        self.command_set = CommandSet(self)
        self.command_set.register([
            Command("peon", commands.cmd_peon),
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
            Command("doc", commands.cmd_doc,
                    description="your personal psychotherapist hotline",
                    examples=["{0} life is hard, man.."]),
            Command("morse", commands.cmd_morse,
                    description="attempt to translate to/from morse code",
                    examples=["{0} sos"]),
            Command("stats", commands.cmd_stats, description="print various peon stats"),
            MentionHandler(commands.handle_simple_replies),
            MentionHandler(commands.handle_emergency_party_mention),
        ])
        self.start_time = datetime.now()

    def run(self):
        """Run peon."""

        client_params = {
            "max_messages": 3000,
            "activity": discord.Game(name=self.GAME_NAME),
            "heartbeat_timeout": 30,
        }

        self._client = discord.Client(**client_params)

        @self.client.event
        async def on_ready():
            await self._client.user.edit(username=self.NAME, avatar=self.AVATAR)
            print("Logged in as\n{0}\n{1}\n------".format(
                self._client.user.name, self.client.user.id))

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return

            await self.command_set.execute(message)

        self._client.run(self.env_vars[ENV_TOKEN])
