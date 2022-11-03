"""Peon handlers."""

import functools
import os
import re
from datetime import datetime

from peon_common import exceptions, utils
from peon_telegram import constants
from peon_common.exceptions import (
    CommandAccessRestricted,
    CommandExecutionError,
    CommandMalformed,
)

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


def admins():
    """Return a list of telegram admin user names."""

    return [name for name
            in os.environ.get(utils.ENV_TELEGRAM_ADMINS, "").split(",")
            if re.match(constants.USER_NAME_REGEX, name)]


def default_handler(command_override: str = None,
                    require_input: bool = False,
                    examples: list[str] = None,
                    reply: bool = False,
                    admin: bool = False,
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

                text = update.message.text[len(command) + 1:].strip()
                print(f"DEBUG: ({datetime.now().strftime('%Y %b, %d %l:%M%p')}) "
                      f"({update.effective_user.name}) '{command}' -> '{text}'")

                if admin and update.effective_user.name not in admins():
                    raise CommandAccessRestricted()
                if require_input and not text:
                    raise CommandMalformed()

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=callable(text),
                    reply_to_message_id=update.message.id if reply else None)
            except CommandMalformed as cm:
                if examples:
                    variations = "\n".join(f"\t`{constants.PREFIX}{command} {body}`"
                                            for body in examples)
                    err_msg = f"Examples:\n{variations}"
                else:
                    err_msg = "No input provided"
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=err_msg,
                    parse_mode=tgconstants.ParseMode.MARKDOWN_V2,
                    reply_to_message_id=update.message.id)
                print(type(cm))
            except CommandAccessRestricted as car:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text="Admin privileges required.",
                                               reply_to_message_id=update.message.id)
                print(type(car))
            except CommandExecutionError as cee:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text="Command unsuccessful.",
                                               reply_to_message_id=update.message.id)
                print(type(cee))
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(f"Caught error:\n```{e}```" if constants.DEBUG else
                          "¯\\\\\_😫\_/¯"),
                    parse_mode=tgconstants.ParseMode.MARKDOWN_V2,
                    reply_to_message_id=update.message.id)
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


@default_handler(reply=True, admin=True)
def test(text):
    return "..."


@default_handler()
def help(text):
    return "help?!"


@default_handler(require_input=True, examples= ["d4", "2d8 + d12", "100", "12-80"])
def roll(text):
    return f"{text}:\n{utils.roll(text.replace('+', ' ').split())}"


@default_handler(command_override="tr",
                 require_input=True,
                 examples=["<text..>",
                           "<lang_to> <text..>",
                           "<lang_from> <lang_to> <text..>"])
def translate(text):
    words = text.split()
    lang_from = None
    lang_to = None

    if words and len(words[0]) == 2 and words[0] in utils.langs:
        lang_to = words[0]
        del words[0]
    if words and len(words[0]) == 2 and words[0] in utils.langs:
        lang_from = lang_to
        lang_to = words[0]
        del words[0]
    if not words:
        raise exceptions.CommandMalformed()

    result = utils.translate(" ".join(words), lang_from=lang_from, lang_to=lang_to)

    return f"({result['lang']}) {result['text']}"


@default_handler(require_input=True,
                 examples=["hello", "--. .. -... -... . .-. .. ... ...."])
def morse(text):
    return utils.morse_helper(text)


@default_handler(reply=True,
                 require_input=True,
                 examples=["unstoppable force vs immovable object"])
def mangle(text):
    return utils.mangle(text)


@default_handler(require_input=True,
                 examples=["Every 60 seconds in Africa a minute passes"])
def starify(text):
    return utils.starify(text)


@default_handler(command_override="8ball", reply=True)
def ask_8ball(text):
    return utils.ask_8ball()


@default_handler(require_input=True, examples=["neon"])
def wiki(text):
    try:
        return utils.wiki_summary(text)
    except exceptions.CommandExecutionError:
        return "Article not found"


@default_handler(require_input=True, examples=["topkek"])
def urban(text):
    word, descr, examples, _ = utils.urban_query(os.environ[utils.ENV_TOKEN_RAPIDAPI],
                                                 text)
    return f"{word}:\n{descr}\n\nexamples:\n{examples}"


@default_handler(reply=True, require_input=True)
def doc(text):
    return utils.doc(text)


@default_handler(reply=True,
                 require_input=True,
                 examples=["user profile", "user game_count", "user gibberish"])
def steam(text):
    try:
        return utils.steam(text)
    except exceptions.CommandError as e:
        return str(e)
    except:
        raise


@default_handler(reply=True, require_input=True, examples=["bcgfycrfz byrdbpbwbz"])
def punto(text):
    return utils.punto(text)


@default_handler(reply=True, require_input=True, examples=["опачки"])
def translitify(text):
    return utils.translitify(text.lower())


@default_handler(reply=True, require_input=True)
def reverse(text):
    return text[::-1]


@default_handler(admin=True, command_override="r")
def resource_usage(text):
    return utils.resource_usage(text)


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
