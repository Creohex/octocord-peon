"""Command model, definitions and command/handler sets for discord client."""

import os
import random
import re
import time

from abc import abstractmethod
from datetime import datetime

from peon import utils


async def reply(message, text):
    """Reply to the message with text (returns new message object)."""

    if text:
        if isinstance(text, str) and len(text) > 2000:
            text = "{0}...".format(text[:1996])

        return await message.channel.send(text)


async def handle_simple_replies(message, **kwargs):
    """Scan messages for keywords and reply accordingly."""

    payload = utils.normalize_text(
        message.content, simple_mask=True, do_de_latinize=True)

    for k, v in utils.simple_replies_collection.items():
        if k in payload:
            chance, phrases = v
            if len(phrases) > 0 and chance >= random.randint(0, 100):
                await reply(message, random.choice(phrases))
                return True

    return False


async def handle_emergency_party_mention(message, **kwargs):
    """Reply to random emergency member if role is mentioned."""

    if utils.role_emergency in message.content:
        members = []
        for m in message.channel.guild.members:
            for r in m.roles:
                if r.id == utils.role_emergency_raw:
                    members.append(m)

        if len(members) > 0:
            await reply(message,
                        "{0} {1}".format(random.choice(members).mention,
                                         random.choice(utils.emergency_phrases)))
            return True

    return False


async def cmd_peon(message, content, **kwargs):
    """List available commands."""

    commands = [cmd for cmd in kwargs.get("command_set").commands
                if isinstance(cmd, Command)]
    descriptions = []

    for command in commands:
        info = command.prefix_full
        if command.description:
            info = "{0} - {1}".format(info, command.description)
        if command.examples:
            info = "{0}\n\t{1}".format(info, "\n\t".join(
                [example.format(command.prefix_full) for example in command.examples]))

        descriptions.append(info)

    await reply(message, "Available commands:\n{0}".format("\n".join(descriptions)))


async def cmd_test(message, content, **kwargs):
    """Test function."""

    await reply(message, "test - {0}".format(content))


async def cmd_tr(message, content, **kwargs):
    """Translate text using available translation services.

    Formats:
        !tr <text> - translate <text> into russian (by default);
        !tr<lang> <text> - translate <text> into <lang>;
        !tr<lang_1><lang_2> <text> - translate <text> from <lang_1> to <lang_2>.
    Language parameters must be in 2-char notation.
    """

    prefix = message.content.split()[0]
    text = message.content[len(prefix)+1:]
    result = ""

    if len(prefix) == 3:
        result = utils.translate(text)
    elif len(prefix) == 5:
        result = utils.translate(text, lang_to=prefix[3:5])
    elif len(prefix) == 7:
        result = utils.translate(text, lang_from=prefix[3:5],
                                       lang_to=prefix[5:7])
    else:
        await reply(message,
                    "Correct format: !tr <text..> | !tr<lang_to> <text..> |"
                    " !tr<lang_from><lang_to> <text..>\n(lang = en|es|fi|ru|...)")
        return

    await reply(message, "({0}) {1}".format(result["lang"], result["text"]))


async def cmd_roll(message, content, **kwargs):
    """Dice rolls.

    Dice combinations can be passed in various forms, for example:
        !roll d12 - rolls 12-sided dice
        !roll 100 - rolls 100-sided dice
        !roll 2d4+d5 + 2d8 - rolls two 4-sided, one 5-sided and two 8-sided dice
        !roll 59-211 - rolls random value between 59 and 211
        !roll L9 - rolls alexeys for 9 frames
    (Single responsibility principle has been neglected here in a bad way.)
    """

    text = utils.normalize_text(message.content.lower(), markdown=True)
    raw = re.split(r' ?\+ ?', re.split(r'!roll ', text)[1])

    try:
        if not len(raw):
            raise Exception("Args required (cmd: {0})".format(text))

        if "l" in raw[0]:
            real_alexeys = [utils.format_emoji(e)
                            for e
                            in message.channel.guild.emojis
                            if e.name in utils.rolling_alexeys]
            text = " ".join(
                [real_alexeys[_ % 2]
                for _
                in range(min(int(re.split('l', raw[0].lower())[1]), 200))])
            await reply(message, text)
            await message.delete()
        else:
            await reply(message, utils.roll(raw))

    except Exception as e:
        await message.add_reaction(emoji="😫")
        raise e


async def cmd_starify(message, content, **kwargs):
    """Generate string resemblint star sky with ASCII symbols and spread text evenly."""

    if len(content) > 0:
        await reply(message, utils.starify(content))
        await message.delete()


async def cmd_slot(message, content, **kwargs):
    """Slot machine simulation."""

    static_emojis = [e for e in message.channel.guild.emojis if not e.animated]
    sequence, success = utils.slot_sequence(static_emojis)

    msg = await reply(message, message.author)
    time.sleep(1)
    for s in sequence:
        await msg.edit(content=s)
        time.sleep(1)

    await msg.add_reaction(emoji="🎊" if success else "😫")

    if success:
        await reply(
            message,
            random.choice(utils.slot_grats).format(
                utils.format_user(message.author))
            if random.choice([0,1])
            else utils.translate(
                random.choice(utils.generic_grats),
                lang_from="en", lang_to=random.choice(utils.langs)
            )["text"]
        )


async def cmd_wiki(message, content, **kwargs):
    """Query wikipedia and return results.

    Since this wiki API does not support a search function, spaces in
    message content are replaced with underscores to have a better chance
    of querying the correct page.
    """

    if len(content) > 0:
        content = "_".join(content.split(" "))
        await reply(message, utils.wiki_summary(content))


async def cmd_urban(message, content, **kwargs):
    """Query urban dictionary."""

    if len(content) > 0:
        defs = utils.urban_query(os.environ.get(utils.ENV_RAPIDAPI_TOKEN), content)
        if defs is None:
            await message.add_reaction(emoji="😫")
        else:
            word, description, examples, _ = defs
            text = "{0}:\n{1}\n\nexamples:\n{2}".format(word, description, examples)
            await reply(message, text)


async def cmd_stats(message, content, **kwargs):
    """Prints peon stats."""

    data = {}
    peon = kwargs.get("client")
    client = peon.client
    commands = kwargs.get("command_set").commands

    data["user"] = client.user.name
    data["latency"] = client.latency
    delta = datetime.now() - peon.start_time
    data["uptime"] = "{0} days, {1} hours, {2} minutes, {3} seconds".format(
        delta.days, delta.seconds // 3600, delta.seconds % 3600 // 60, delta.seconds % 60)
    data["guild count"] = len(client.guilds)
    data["guilds"] = ", ".join("{0} ({1})".format(guild.name, guild.owner.name)
                               for guild in client.guilds)
    data["commands"] = len(commands)
    data["cached messages"] = len(client.cached_messages)
    data["private channels"] = len(client.private_channels)
    data["voice clients"] = len(client.voice_clients)

    await reply(message, "\n".join("{0}: {1}".format(k, v) for k, v in data.items()))


async def cmd_scramble(message, content, **kwargs):
    """Scramble text by consequently translating through multiple languages."""

    text = utils.translate(content, lang_to="en")["text"]
    lang_from = "en"
    lang_sequence = [random.choice(utils.langs) for _ in range(6)] + ["ru"]

    for l in lang_sequence:
        translated = utils.translate(text, lang_from=lang_from, lang_to=l)
        lang_from = l
        text = translated["text"]

    await reply(message, text)


class BaseCommand():
    """Abstract command class."""

    def __init__(self, description=None, examples=None):
        self.description = description
        self.examples = examples or []

    @abstractmethod
    async def execute(self, message, **kwargs):
        """Execute command based on the message provided."""

        raise NotImplementedError()


class Command(BaseCommand):
    """Peon command object."""

    CMD_SIGN = "!"
    """Command sign."""

    @property
    def prefix_full(self):
        """Returns complete prefix."""

        return "{0}{1}".format(self.CMD_SIGN, self.prefix)

    @property
    def content_offset(self):
        """Returns content string offset."""

        return len(self.prefix_full) + 1

    def __init__(self, prefix, func, **kwargs):
        """Initialize `Command` object.

        Function must have `message` object as first positional argument
        and `content` string (containing function-related data) as
        second positional argument.
        """

        super(Command, self).__init__(**kwargs)

        if not isinstance(prefix, str):
            raise Exception("prefix '{0}' is not a string!".format(prefix))
        if not callable(func) or func.__code__.co_argcount != 2:
            raise Exception(
                "'func' must be a function with strictly two positional args!")

        self.prefix = prefix
        self.func = func

    async def execute(self, message, **kwargs):
        """Execute function."""

        if message.content.lower().startswith(self.prefix_full):
            try:
                await self.func(message, message.content[self.content_offset:], **kwargs)
                return True
            except Exception as e:
                await message.add_reaction(emoji="😫")
                raise Exception(e)

        return False


class MentionHandler(BaseCommand):
    """Represents chat mention handler object."""

    def __init__(self, handler, **kwargs):
        """Initialize `MentionHandler` object.

        Expecting single function argument, which must expect
        `discord.Message` object as single positional argument.
        """

        super(MentionHandler, self).__init__(**kwargs)

        if not callable(handler) or handler.__code__.co_argcount != 1:
            raise Exception(
                "'handler' must be a function with strictly one positional arg!")

        self.func = handler

    async def execute(self, message, **kwargs):
        """Execute handler."""

        return await self.func(message, **kwargs)


class CommandSet():
    """Represents bot command set."""

    def __init__(self, discord_client):
        self.discord_client = discord_client
        self.commands = []

    def register(self, commands):
        """Register commands."""

        if not all(isinstance(command, BaseCommand) for command in commands):
            raise Exception("'command' object must inherit from `BaseCommand`.")

        self.commands.extend(commands)

    async def execute(self, message):
        """Executes commands in order and terminates after first successful command."""

        for command in self.commands:
            if await command.execute(message, client=self.discord_client,
                                              command_set=self):
                return
