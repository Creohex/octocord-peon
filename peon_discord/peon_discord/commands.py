"""Command model, definitions and command/handler sets for discord client."""

import os
import random
import re
import time
from abc import abstractmethod
from datetime import datetime

from discord.enums import ChannelType

from peon_common import (
    exceptions,
    functions,
    utils,
)
from peon_common.gpt import Completion


CMD_SIGN = "!"
"""Character signifying the start of a command that has to be handled."""
ALTERNATIVE_CMD_SIGNS = ["@"]
"""Command signs that can alternative be used."""

SENDER_PATTERN = r"^\[\[\w+\]\([\w:\/\-\.\#\!]+\)\]:\s"
"""A regexp pattern for messages that contain sender hyperlink."""

GENERIC_GRATS = [
    "Congratulations!",
    "wow, unbelievable",
    "Once in a lifetime achievement!",
    "Incredible!",
    "Absolutely gorgeous outcome!",
    "Well done!",
]
""""""


def mention_format(user_id):
    """Decorates discord user ID to mention format."""

    return f"<@{user_id}>"


async def reply(message, text, mention_message=False):
    """Reply to the message with text (returns new message object)."""

    if text:
        if isinstance(text, str) and len(text) > 2000:
            text = f"{text[:1996]}..."
        return await message.channel.send(
            text,
            reference=message if mention_message else None,
        )


async def handle_simple_replies(message, **kwargs):
    """Scan messages for keywords and reply accordingly."""

    payload = functions.normalize_text(
        message.content, simple_mask=True, do_de_latinize=True
    )

    for k, v in functions.simple_replies_collection.items():
        if k in payload:
            chance, phrases = v
            if len(phrases) > 0 and chance >= random.randint(0, 100):
                await reply(message, random.choice(phrases))
                return True

    return False


async def cmd_help(message, content, **kwargs):
    """List available commands."""

    commands = [
        cmd for cmd in kwargs.get("command_set").commands if isinstance(cmd, Command)
    ]
    descriptions = []

    for command in commands:
        full_prefix = f"{CMD_SIGN}{command.prefix}"
        info = full_prefix
        if command.description:
            info = f"- {info} - {command.description}"
        if command.examples:
            examples = "\n * ".join(
                [example.format(full_prefix) for example in command.examples]
            )
            info = f"{info}\n * {examples}"

        descriptions.append(info)

    await reply(
        message, "__**Available commands**__:\n{0}".format("\n".join(descriptions))
    )


async def cmd_test(message, content, **kwargs):
    """Test function."""

    await reply(message, f"test - {content}")


async def cmd_tr(message, content, **kwargs):
    """Translate text using available translation services.

    Formats:
        !tr <text> - translate <text> into english (by default);
        !tr<lang> <text> - translate <text> into <lang>;
        !tr<lang_1><lang_2> <text> - translate <text> from <lang_1> to <lang_2>.
    Language parameters must be in 2-char notation.
    """

    try:
        result = functions.translate_helper(message.content)
        await reply(message, f"({result['lang']}) {result['text']}")
    except exceptions.CommandMalformed:
        await reply(
            message,
            "Correct format: !tr <text..> | !tr<lang_to> <text..> |"
            " !tr<lang_from><lang_to> <text..>\n(lang = en|es|fi|ru|...)",
        )


async def cmd_roll(message, content, **kwargs):
    """Dice rolls.

    Dice combinations can be passed in various forms, for example:
        !roll d12 - rolls 12-sided dice
        !roll 100 - rolls 100-sided dice
        !roll 2d4+d5 + 2d8 - rolls two 4-sided, one 5-sided and two 8-sided dice
        !roll 59-211 - rolls random value between 59 and 211
    (Single responsibility principle has been neglected here in a bad way.)
    """

    text = functions.normalize_text(message.content.lower(), markdown=True)
    raw = re.split(r" ?\+ ?", re.split(r"roll ", text)[1])

    try:
        if not len(raw):
            raise Exception(f"Args required (cmd: {text})")

        await reply(message, functions.roll(raw))

    except Exception as e:
        await message.add_reaction(emoji="😫")
        raise e


async def cmd_starify(message, content, **kwargs):
    """Generate string resemblint star sky with ASCII symbols and spread text evenly."""

    if len(content) > 0:
        await reply(message, functions.starify(content))
        await message.delete()


async def cmd_slot(message, content, **kwargs):
    """Slot machine simulation."""

    static_emojis = [e for e in message.channel.guild.emojis if not e.animated]
    sequence, success = functions.slot_sequence(static_emojis)

    msg = await reply(message, message.author)
    time.sleep(1)
    for s in sequence:
        await msg.edit(content=s)
        time.sleep(1)

    await msg.add_reaction(emoji="🎊" if success else "😫")

    if success:
        await reply(
            message,
            (
                random.choice(GENERIC_GRATS).format(functions.format_user(message.author))
                if random.choice([0, 1])
                else functions.translate(
                    random.choice(GENERIC_GRATS),
                    lang_from="en",
                    lang_to=random.choice(functions.langs),
                )["text"]
            ),
        )


async def cmd_wiki(message, content, **kwargs):
    """Query wikipedia and return results.

    Since this wiki API does not support a search function, spaces in
    message content are replaced with underscores to have a better chance
    of querying the correct page.
    """

    if len(content) > 0:
        content = "_".join(content.split(" "))
        await reply(message, functions.wiki_summary(content))


async def cmd_urban(message, content, **kwargs):
    """Query urban dictionary."""

    if len(content) > 0:
        defs = functions.urban_query(os.environ[utils.ENV_TOKEN_RAPIDAPI], content)
        if defs is None:
            await message.add_reaction(emoji="😫")
        else:
            word, description, examples, _ = defs
            text = f"{word}:\n{description}\n\nexamples:\n{examples}"
            await reply(message, text)


async def cmd_stats(message, content, **kwargs):
    """Prints peon stats."""

    data = {}
    peon = kwargs.get("client")
    client = peon.client
    commands = kwargs.get("command_set").commands

    data["user"] = client.user.name
    data["latency"] = f"{client.latency:.2f}"
    delta = datetime.now() - peon.start_time
    data["uptime"] = "{0} days, {1} hours, {2} minutes, {3} seconds".format(
        delta.days, delta.seconds // 3600, delta.seconds % 3600 // 60, delta.seconds % 60
    )
    data["guild count"] = len(client.guilds)
    data["guilds"] = ", ".join(guild.name for guild in client.guilds)
    data["commands"] = len(commands)
    data["cached messages"] = len(client.cached_messages)
    data["private channels"] = len(client.private_channels)
    data["voice clients"] = len(client.voice_clients)

    formatted = "\n".join(f"{k}: {v}" for k, v in data.items())
    await reply(message, f"```{formatted}```")


async def cmd_mangle(message, content, **kwargs):
    """Mangle command wrapper."""

    await reply(message, functions.mangle(content))


async def cmd_doc(message, content, **kwargs):
    """Eliza psychotherapist hotline."""

    await reply(message, functions.doc(content))


async def cmd_morse(message, content, **kwargs):
    """Attempt to translate to or from morse code."""

    await reply(message, functions.morse_helper(content))


async def cmd_8ball(message, content, **kwargs):
    """Fetch 8ball message."""

    await reply(
        message, f"{functions.format_user(message.author)} {functions.ask_8ball()}"
    )


async def cmd_punto(message, content, **kwargs):
    """Attempt to punto switch provided message."""

    if not content:
        raise Exception("Content required")

    await reply(message, functions.punto(content.lower()))


async def cmd_translitify(message, content, **kwargs):
    """Attempt to convert content into gibberish translit."""

    await reply(message, functions.translitify(content.lower()))


async def cmd_reverse(message, content, **kwargs):
    """Reverse given text."""

    if not content:
        raise Exception("Content required")

    await reply(message, content[::-1])


async def cmd_ah_query(message, content, **kwargs):
    """Query AH prices for linked items."""

    if not content:
        raise Exception("Content required")

    await reply(message, functions.ah_query(content))


def sanitize_gpt_request(text, mention):
    """GPT prompt sanitizer."""

    pattern = r"^(\[\[(?P<user>[a-zA-Z]+)\]\(.*\)\]:\s)?(?P<message>.*)$"
    match = re.search(pattern, text)
    result = match.group("message")

    if match.group("user"):
        result = f"{match.group('user')} says: {match.group('message')}"

    return re.sub(re.escape(mention), "you", result)


async def cmd_gpt(message, content, **kwargs):
    """Make a GPT request."""

    mention = mention_format(kwargs["client"].client.user.id)
    if not re.search(mention, message.content.lower()):
        return False

    match message.channel.type:
        case ChannelType.text:
            chat_owner_id = message.channel.guild.id
        case ChannelType.private:
            chat_owner_id = message.author.id
        case _:
            raise Exception("Unsupported channel type")

    print(f"DEBUG: handling GPT request: '{content}'")
    try:
        answer = Completion().request(
            sanitize_gpt_request(message.content, mention),
            owner_id=str(chat_owner_id),
            use_history=True,
            history_limit=3,
        )
    except Exception as e:
        print(f"DEBUG: Completion error: {str(e)}")
        await reply(message, "something went wrong ;(", mention_message=True)
        return True
    print(f"DEBUG: reply: '{answer}'")

    await reply(message, answer, mention_message=True)
    return True


class BaseCommand:
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

    def __init__(self, prefix, func, **kwargs):
        """Initialize `Command` object.

        Function must have `message` object as first positional argument
        and `content` string (containing function-related data) as
        second positional argument.
        """

        super().__init__(**kwargs)

        if not isinstance(prefix, str):
            raise Exception(f"prefix '{prefix}' is not a string!")
        if not callable(func) or func.__code__.co_argcount != 2:
            raise Exception(
                "'func' must be a function with strictly two positional args!"
            )

        self.prefix = prefix
        self.func = func

    async def execute(self, message, **kwargs):
        """Execute function."""

        if not message.content.startswith(self.prefix):
            return False

        try:
            print(f'DEBUG: executing "{message.content}"')
            await self.func(message, message.content[len(self.prefix) + 1 :], **kwargs)
            return True
        except Exception as e:
            await message.add_reaction(emoji="😫")
            raise Exception(e)


class MentionHandler(BaseCommand):
    """Represents chat mention handler object."""

    def __init__(self, handler, **kwargs):
        """Initialize `MentionHandler` object.

        Expecting single function argument, which must expect
        `discord.Message` object as single positional argument.
        """

        super().__init__(**kwargs)
        self.func = handler

    async def execute(self, message, **kwargs):
        """Execute handler."""

        # TODO: handle exceptions, print reasons in specific cases?
        return await self.func(message, message.content, **kwargs)


class CommandSet:
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

        if message.content.startswith("["):
            sender_link = re.match(SENDER_PATTERN, message.content)
            if sender_link:
                message.content = message.content[len(sender_link.group()) :].strip()

        if message.content.startswith(CMD_SIGN) or any(
            message.content.startswith(c) for c in ALTERNATIVE_CMD_SIGNS
        ):
            message.content = message.content[1:]

        for command in self.commands:
            if await command.execute(
                message,
                client=self.discord_client,
                command_set=self,
            ):
                break
