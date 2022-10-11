"""Peon handlers."""

import functools
import os

from peon_common import exceptions, utils
from peon_telegram import constants

from telegram import (
    constants as tgconstants,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)


HANDLERS = []
"""Handlers to be registered in telegram client."""


# TODO: input requirement flag/regex?
def default_handler(command_override: str = None,
                    keep_prefix: bool = False,
                    reply: bool = False,
):
    """Basic handler wrapper."""

    def decorator(callable):
        print("DEBUG: registering handler: "
              f"{command_override if command_override else callable.__name__}")
        command = command_override or callable.__name__

        @functools.wraps(callable)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                # TODO: handle edits (update.message.edit_text)
                if getattr(update.message, "text", None) is None:
                    return

                text = (update.message.text[1:] if keep_prefix else
                        update.message.text[len(command) + 1:].strip())
                print(f"DEBUG: '{command}' -> '{text}'")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=callable(text),
                    reply_to_message_id=update.message.id if reply else None)
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(f"Caught error:\n```{e}```" if constants.DEBUG else
                          "¯\\\\\_😫\_/¯"),
                    parse_mode=tgconstants.ParseMode.MARKDOWN_V2)
                raise e

        HANDLERS.append(CommandHandler(command, wrapper))
    return decorator


def inline_handler(callable):
    """Inline handler wrapper."""

    print(f"DEBUG: registering inline handler: '{callable.__name__}'")

    @functools.wraps(callable)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.inline_query.query:
                return
            await context.bot.answer_inline_query(update.inline_query.id,
                                                  callable(update.inline_query.query))
        except Exception as e:
            print(f"Caught exception during handling {callable.__name__}:\n```{e}```")
            return

    HANDLERS.append(InlineQueryHandler(wrapper))


@default_handler()
def test(text):
    return "..."


@default_handler(keep_prefix=True)
def help(text):
    return "..."


@default_handler()
def roll(text):
    return f"{text}:\n{utils.roll(text.replace('+', ' ').split())}"


@default_handler(command_override="tr")
def translate(text):
    try:
        words = text.split()
        lang_from = None
        lang_to = None

        if words and len(words[0]) == 2 and words[0] in utils.langs:
            lang_from = words[0]
            del words[0]
        if words and len(words[0]) == 2 and words[0] in utils.langs:
            lang_to = words[0]
            del words[0]
        if not words:
            raise exceptions.CommandMalformed(f"Invalid translation command '{text}'")

        result = utils.translate(" ".join(words), lang_from=lang_from, lang_to=lang_to)

        return f"({result['lang']}) {result['text']}"
    except exceptions.CommandMalformed:
        return ("Correct format:\n/tr <text..>\n/tr <lang_to> <text..>\n"
                "/tr <lang_from> <lang_to> <text..>\nlangs: en, es, fi, ru, ...")


@default_handler(reply=True)
def mangle(text):
    return utils.mangle(text)


@default_handler()
def starify(text):
    return utils.starify(text)


@default_handler(command_override="8ball", reply=True)
def ask_8ball(text):
    return utils.ask_8ball()


@default_handler()
def wiki(text):
    try:
        return utils.wiki_summary(text)
    except exceptions.CommandExecutionError:
        return "Article not found"


@default_handler()
def urban(text):
    word, descr, examples, _ = utils.urban_query(os.environ[utils.ENV_TOKEN_RAPIDAPI],
                                                 text)
    return f"{word}:\n{descr}\n\nexamples:\n{examples}"


@default_handler(reply=True)
def doc(text):
    return utils.doc(text)


@default_handler(reply=True)
def steam(text):
    try:
        return utils.steam(text)
    except exceptions.CommandError as e:
        return str(e)
    except:
        raise


@default_handler(reply=True)
def punto(text):
    return utils.punto(text)


@default_handler(reply=True)
def translitify(text):
    return utils.translitify(text.lower())


@default_handler(reply=True)
def reverse(text):
    return text[::-1]


@inline_handler
def inline_test(query):
    return [
        InlineQueryResultArticle(
            id="starify",
            title="starify",
            input_message_content=InputTextMessageContent(utils.starify(query)),
            description="Adds feelings and a mystical sense to a sentence"),
        InlineQueryResultArticle(
            id="roll",
            title="roll",
            input_message_content=InputTextMessageContent(utils.roll(query)),
            description="d4 | 2d8 | 100 | 42-59 | 2d5+100+4d4",),
    ]
