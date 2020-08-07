import binascii
import json
import os
import random
import re
import requests
import time
import urllib.parse

from peon import utils


async def reply(message, text):
    if text:
        if isinstance(text, str) and len(text) > 2000:
            text = "{0}...".format(text[:1996])

        return await message.channel.send(text)


async def handle_simple_replies(message):
    payload = utils.normalize_text(
        message.content, simple_mask=True, do_de_latinize=True)
    for k, v in utils.simple_replies_collection.items():
        if k in payload:
            chance, phrases = v
            if len(phrases) > 0 and chance >= random.randint(0, 100):
                return await reply(message, random.choice(phrases))


async def handle_emergency_party_mention(message):
    if utils.role_emergency in message.content:
        # get all members of this role
        members = []
        for m in message.channel.guild.members:
            for r in m.roles:
                if r.id == utils.role_emergency_raw:
                    members.append(m)

        if len(members) == 0:
            return False

        # mention member and write something
        return await reply(
            message, "{0} {1}".format(
                random.choice(members).mention, random.choice(utils.emergency_phrases)))


async def cmd_peon(message, content):
    return await reply(
        message, "Available commands:\n{0}".format("\n".join(utils.peon_commands)))


async def cmd_test(message, content):
    return await reply(message, "test - {0}".format(content))


async def cmd_tr(message, content):
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
        return await reply(
            message,
            "Correct format: !tr <text..> | !tr<lang_to> <text..> |"
            " !tr<lang_from><lang_to> <text..>\n(lang = en|es|fi|ru|...)"
        )

    return await reply(message, "({0}) {1}".format(result["lang"], result["text"]))


async def cmd_roll(message, content):
    text = utils.normalize_text(message.content.lower(), markdown=True)
    raw = re.split(r' ?\+ ?', re.split(r'!roll ', text)[1])

    try:
        if not len(raw):
            raise Exception("Args required (cmd: {0})".format(text))

        if "l" in raw[0]:
            real_alexeys = utils.format_emojis(filter(
                lambda e: e.name in utils.rolling_alexeys,
                message.channel.guild.emojis))
            text = " ".join(
                [real_alexeys[_ % 2] for _
                    in range(min(int(re.split('l', raw[0].lower())[1]), 200))]
            )
            await reply(message, text)
            await message.delete()
        else:
            await reply(message, utils.roll(raw))

        return
    except Exception as e:
        await message.add_reaction(emoji="😫")
        raise e


async def cmd_starify(message, content):
    if message.content.startswith("!starify "):
        text = message.content[9:]
        if len(text) > 0:
            await reply(message, utils.starify(text))
            await message.delete()
        return


async def cmd_slot(message, content):
    # !slot
    if message.content == "!slot":
        sequence, success = utils.slot_sequence(message.channel.guild.emojis)

        msg = await reply(message, message.author)
        time.sleep(1)
        for s in sequence:
            await msg.edit(content=s)
            time.sleep(1)

        await msg.add_reaction(emoji="🎊" if success else "😫")

        if success:
            return await reply(
                message,
                random.choice(utils.slot_grats).format(
                    utils.format_user(message.author))
                if random.choice([0,1])
                else utils.translate(
                        random.choice(utils.generic_grats),
                        lang_from="en", lang_to=random.choice(utils.langs)
                        )["text"]
                )


async def cmd_wiki(message, content):
    # !wiki
    if message.content.startswith("!wiki "):
        query = message.content[6:]
        if len(query) > 0:
            query = "_".join(query.split(" "))
            return await reply(message, utils.wiki_summary(query))


async def cmd_urban(message, content):
    # !urban
    if message.content.startswith("!urban "):
        query = message.content[7:]

        if len(query) > 0:
            defs = utils.urban_query(os.environ.get(utils.ENV_RAPIDAPI_TOKEN), query)
            if defs is None:
                return await message.add_reaction(emoji="😫")
            else:
                word, description, examples, _ = defs
                text = "{0}:\n{1}\n\nexamples:\n{2}".format(
                    word, description, examples)
                return await reply(message, text)


class Command():
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

    def __init__(self, prefix, func):
        """Initialize `Command` object.

        Function must have `message` object as first positional argument
        and `content` string (containing function-related data) as
        second positional argument.
        """

        if not isinstance(prefix, str):
            raise Exception("prefix '{0}' is not a string!".format(prefix))
        if not callable(func) or func.__code__.co_argcount != 2:
            raise Exception(
                "'func' must be a function with strictly two positional args!")

        self.prefix = prefix
        self.func = func

    async def execute(self, message):
        """Execute function."""

        if message.content.startswith(self.prefix_full):
            try:
                await self.func(message, message.content[self.content_offset:])
                return True
            except Exception as e:
                await message.add_reaction(emoji="😫")
                raise Exception(e)

        return False


commands = [
    Command("peon", cmd_peon),
    Command("test", cmd_test),
    Command("tr", cmd_tr),
    Command("roll", cmd_roll),
    Command("starify", cmd_starify),
    Command("slot", cmd_slot),
    Command("wiki", cmd_wiki),
    Command("urban", cmd_urban),
]
"""Command dictionary."""


mention_handlers = [
    handle_simple_replies,
    handle_emergency_party_mention,
]
"""Message content-related reactions (if no commands were executed)"""
