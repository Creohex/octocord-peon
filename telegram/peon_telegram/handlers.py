"""Peon handlers."""

import os
import random
import re
import time
from datetime import datetime

import nltk.chat.eliza
import steamapi
from peon_common import utils
from telegram import Update, InputTextMessageContent, InlineQueryResultArticle
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, InlineQueryHandler

# TODO: Add command/inline handlers for all existing commands;
#       Read/think about other ways to handle tg queries

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a bot, please talk to me!")


async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = [
        InlineQueryResultArticle(
            id="starify",
            title="starify",
            input_message_content=InputTextMessageContent(utils.starify(query)),
            description="Adds feelings and a mystical sense to a sentence"),
    ]
    await context.bot.answer_inline_query(update.inline_query.id, results)


HANDLERS = [CommandHandler("test", test),
            InlineQueryHandler(inline_handler)]
