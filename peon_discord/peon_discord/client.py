"""Discord client."""

import discord
from datetime import datetime

from . import commands, CommandSet, Command, MentionHandler
from peon_common.db import initialize_db
from peon_common.utils import (
    get_env_vars,
    get_file,
    ENV_TOKEN_DISCORD,
)


class Peon():
    """Discord Peon client."""

    NAME = "Peon"
    GAME_NAME = "work work"
    AVATAR = get_file(f"{NAME}.png")
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
            Command("help", commands.cmd_help),
            Command("tr", commands.cmd_tr,
                    description="translate text (langs - en, et, ru, be, ...)",
                    examples=["{0} bla", "{0}<to_lang> bla",
                              "{0}<from_lang><to_lang> bla"]),
            Command("mangle", commands.cmd_mangle,
                    description="mangle phrase meaning",
                    examples=["{0} Let's see how it turns out!"]),
            Command("roll", commands.cmd_roll,
                    description="roll dice",
                    examples=["{0} d4", "{0} 2d8", "{0} 100",
                              "{0} 42-59", "{0} 2d5+100+4d4"]),
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
            Command("8ball", commands.cmd_8ball,
                    description="ask 8ball for guidance"),
            Command("punto", commands.cmd_punto,
                    description="attempt to decipher text written in incorrect layout",
                    examples=["{0} nbgbxysq fktrctq"]),
            Command("litify", commands.cmd_translitify,
                    description="turn cyrillic text into latin"),
            Command("reverse", commands.cmd_reverse,
                    description="reverse given text",
                    examples=["{0} olleH"]),
            Command("stats", commands.cmd_stats, description="print various peon stats"),
            MentionHandler(commands.cmd_gpt),
        ])
        self.start_time = datetime.now()

    def run(self):
        """Initialize/run discord client."""

        initialize_db()

        self._client = discord.Client(status="work-work",
                                      activity=discord.CustomActivity("work-work"),
                                      max_messages=3000,
                                      heartbeat_timeout=30.0,
                                      intents=discord.Intents.all())

        @self.client.event
        async def on_ready():
            print(f"Logged in as\n{self._client.user.name}\n{self.client.user.id}\n-----")

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return

            await self.command_set.execute(message)

        self._client.run(self.env_vars[ENV_TOKEN_DISCORD])
