"""Peon handlers."""

import functools
import logging
import os
import re

from peon_common import (
    exceptions,
    functions,
    utils,
)
from peon_common.exceptions import (
    CommandAccessRestricted,
    CommandExecutionError,
    CommandMalformed,
)
from peon_common.gpt import Completion
from peon_common.utils import logger
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
    MessageHandler,
    filters,
)


LOG = logger(logging.DEBUG)

HANDLERS = []
"""Handlers to be registered in telegram client."""

MARKDOWN_PARSE_MODE = tgconstants.ParseMode.MARKDOWN
"""Markdown mode to use for outgoing messages."""

INLINE_HANDLER_SPECIAL_CHAR = "&"
"""Character that works as a signal for inline query to compute results."""

ICON_URL_WRITING = "https://cdn-icons-png.flaticon.com/128/2554/2554282.png"
ICON_URL_TEXT = "https://cdn-icons-png.flaticon.com/128/2521/2521903.png"
"""Various icon URLs."""


def admins():
    """Return a list of telegram admin user names."""

    return [
        name
        for name in os.environ.get(utils.ENV_TELEGRAM_ADMINS, "").split(",")
        if re.match(constants.USER_NAME_REGEX, name)
    ]


def gather_context(update) -> dict:
    return {
        "message_author": str(update.message.from_user.id),
    }


def sanitize_markdown(text: str, delim: str = "`") -> str:
    """Assures that non-codeblock underscores are prepended with backslash."""

    return delim.join(
        chunk if index % 2 else re.sub(r"(?<!\+)_", r"\_", chunk)
        for index, chunk in enumerate(text.split(delim))
    )


def default_handler(
    command_override: str = None,
    require_input: bool = False,
    examples: list[str] = None,
    reply: bool = False,
    admin: bool = False,
):
    """Basic handler wrapper."""

    def decorator(callable):
        # TODO: replace underscores with dashes in callable.__name__?
        command = command_override or callable.__name__
        LOG.debug(f"registering handler: {command}")

        @functools.wraps(callable)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                # TODO: handle edits (update.message.edit_text)
                if getattr(update.message, "text", None) is None:
                    return

                text = update.message.text[len(command) + 1 :].strip()
                LOG.info(f"({update.effective_user.name}) '{command}' -> '{text}'")

                if admin and update.effective_user.name not in admins():
                    raise CommandAccessRestricted()
                if require_input and not text:
                    raise CommandMalformed()

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=sanitize_markdown(callable(text, **gather_context(update))),
                    reply_to_message_id=update.message.id if reply else None,
                    parse_mode=MARKDOWN_PARSE_MODE,
                )
            except CommandMalformed as cm:
                if examples:
                    variations = "\n".join(
                        f"\t`{constants.PREFIX}{command} {body}`" for body in examples
                    )
                    err_msg = f"Examples:\n{variations}"
                else:
                    err_msg = "No input provided"
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=err_msg,
                    reply_to_message_id=update.message.id,
                )
                LOG.warning(str(cm))
            except CommandAccessRestricted as car:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Admin privileges required.",
                    reply_to_message_id=update.message.id,
                )
                LOG.warning(str(car))
            except CommandExecutionError as cee:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Command unsuccessful.",
                    reply_to_message_id=update.message.id,
                )
                LOG.warning(str(cee))
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"Caught error:\n```{e}```" if constants.DEBUG else "¯\\\\\_😫\_/¯"
                    ),
                    parse_mode=MARKDOWN_PARSE_MODE,
                    reply_to_message_id=update.message.id,
                )
                raise e

        HANDLERS.append(CommandHandler(command, wrapper))

    return decorator


def inline_handler(callable):
    """Inline handler wrapper."""

    LOG.info(f"Registering inline handler '{callable.__name__}'")

    @functools.wraps(callable)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.inline_query.query
            if not query:
                return
            elif query[-1] != INLINE_HANDLER_SPECIAL_CHAR:
                await context.bot.answer_inline_query(
                    update.inline_query.id,
                    [
                        InlineQueryResultArticle(
                            id="id",
                            title="writing query...",
                            input_message_content=InputTextMessageContent("..."),
                            description=(
                                "Input must end with "
                                f'{INLINE_HANDLER_SPECIAL_CHAR}" character!'
                            ),
                            thumb_url=ICON_URL_WRITING,
                        )
                    ],
                )
            else:
                username = update.effective_user.name
                LOG.debug(f"({username}) handling inline message: '{query}'")
                await context.bot.answer_inline_query(
                    update.inline_query.id, callable(update.inline_query.query[:-1])
                )
        except Exception as e:
            raise e

    HANDLERS.append(InlineQueryHandler(wrapper))


def direct_message_handler(
    admin: bool = False,
    reply: bool = False,
):
    def decorator(callable):
        LOG.debug(f"Registering direct message handler: '{callable.__name__}'")

        @functools.wraps(callable)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                text = update.message.text.strip()
                if not text.startswith("/"):
                    username = update.effective_user.name
                    LOG.debug(f"({username}) handling direct message: '{text}'")
                    # FIXME: Properly escape certain characters for ParseMode.MARKDOWN_V2
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=sanitize_markdown(callable(text, **gather_context(update))),
                        reply_to_message_id=update.message.id if reply else None,
                        parse_mode=MARKDOWN_PARSE_MODE,
                    )
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="There was a problem handling this request 😕",
                    reply_to_message_id=update.message.id,
                )
                raise e

        HANDLERS.append(MessageHandler(filters.TEXT, wrapper))

    return decorator


@default_handler(reply=True, admin=True)
def test(text, **kwargs):
    return "..."


@default_handler()
def help(text, **kwargs):
    return "help?!"


@default_handler(require_input=True, examples=["d4", "2d8 + d12", "100", "12-80"])
def roll(text, **kwargs):
    return f"{text}:\n{functions.roll(text.replace('+', ' ').split())}"


@default_handler(
    command_override="tr",
    require_input=True,
    examples=["<text..>", "<lang_to> <text..>", "<lang_from> <lang_to> <text..>"],
)
def translate(text, **kwargs):
    words = text.split()
    lang_from = None
    lang_to = None

    if words and len(words[0]) == 2 and words[0] in functions.langs:
        lang_to = words[0]
        del words[0]
    if words and len(words[0]) == 2 and words[0] in functions.langs:
        lang_from = lang_to
        lang_to = words[0]
        del words[0]
    if not words:
        raise exceptions.CommandMalformed()

    result = functions.translate(" ".join(words), lang_from=lang_from, lang_to=lang_to)

    return f"({result['lang']}) {result['text']}"


@default_handler(
    require_input=True, examples=["hello", "--. .. -... -... . .-. .. ... ...."]
)
def morse(text, **kwargs):
    return functions.morse_helper(text)


@default_handler(
    reply=True, require_input=True, examples=["unstoppable force vs immovable object"]
)
def mangle(text, **kwargs):
    return functions.mangle(text)


@default_handler(
    require_input=True, examples=["Every 60 seconds in Africa a minute passes"]
)
def starify(text, **kwargs):
    return functions.starify(text)


@default_handler(command_override="8ball", reply=True)
def ask_8ball(text, **kwargs):
    return functions.ask_8ball()


@default_handler(require_input=True, examples=["neon"])
def wiki(text, **kwargs):
    try:
        return functions.wiki_summary(text)
    except exceptions.CommandExecutionError:
        return "Article not found"


@default_handler(require_input=True, examples=["topkek"])
def urban(text, **kwargs):
    word, descr, examples, _ = functions.urban_query(
        os.environ[utils.ENV_TOKEN_RAPIDAPI], text
    )
    return f"{word}:\n{descr}\n\nexamples:\n{examples}"


@default_handler(reply=True, require_input=True)
def doc(text, **kwargs):
    return functions.doc(text)


@default_handler(reply=True, require_input=True, examples=["bcgfycrfz byrdbpbwbz"])
def punto(text, **kwargs):
    return functions.punto(text)


@default_handler(reply=True, require_input=True, examples=["опачки"])
def translitify(text, **kwargs):
    return functions.translitify(text.lower())


@default_handler(reply=True, require_input=True)
def reverse(text, **kwargs):
    return text[::-1]


@default_handler(admin=True, command_override="r")
def resource_usage(text, **kwargs):
    return functions.resource_usage(text)


# GPT-related:
@default_handler(command_override="show_ai_role", reply=True)
def gpt_role_show(text, **kwargs):
    return Completion().get_role(kwargs["message_author"]) or "default role"


@default_handler(command_override="update_ai_role", require_input=True, reply=True)
def gpt_role_set(text, **kwargs):
    Completion().set_role(kwargs["message_author"], text)
    return "role has been updated"


@default_handler(command_override="reset_ai_role", reply=True)
def gpt_role_reset(text, **kwargs):
    Completion().reset_role(kwargs["message_author"])
    return "role has been reset"


# ---

# @inline_handler
# def gpt_inline(query):
#     result = functions.gpt_request(query, role="assistant")
#     return [
#         InlineQueryResultArticle(
#             id=str(uuid.uuid4())[-5:],
#             title="gpt",
#             input_message_content=InputTextMessageContent(f"Query: {query}\n---\n{result}"),
#             description=f"{result[:40]}...",
#             thumb_url=ICON_URL_TEXT,
#         ),
#     ]


@direct_message_handler(reply=True)
def direct_chat(text, **kwargs):
    return Completion().request(
        text, owner_id=kwargs["message_author"], use_history=True, history_limit=3
    )
