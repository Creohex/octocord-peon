"""Various functionality to be used as commands by messaging clients."""

import json
import os
import random
import re
import requests
import socket
import time
import urllib.parse
import yarl
from pathlib import Path

import nltk.chat.eliza
import psutil

from .ah import AHScraper
from .exceptions import (
    CommandExecutionError,
    CommandMalformed,
)


BYTES_GB = 2**30
"""Bytes in a gigabyte."""

MORSE_CODE = {
    "a": ".-",
    "b": "-...",
    "c": "-.-.",
    "d": "-..",
    "e": ".",
    "f": "..-.",
    "g": "--.",
    "h": "....",
    "i": "..",
    "j": ".---",
    "k": "-.-",
    "l": ".-..",
    "m": "--",
    "n": "-.",
    "o": "---",
    "p": ".--.",
    "q": "--.-",
    "r": ".-.",
    "s": "...",
    "t": "-",
    "u": "..-",
    "v": "...-",
    "w": ".--",
    "x": "-..-",
    "y": "-.--",
    "z": "--..",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    ", ": "--..--",
    ".": ".-.-.-",
    "?": "..--..",
    "/": "-..-.",
    "-": "-....-",
    "(": "-.--.",
    ")": "-.--.-",
    " ": " ",
}
"""Morse code dictionary."""

ICOSAHEDRON = [
    "As I see it, yes.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don’t count on it.",
    "It is certain.",
    "It is decidedly so.",
    "Most likely.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Outlook good.",
    "Reply hazy, try again.",
    "Signs point to yes.",
    "Very doubtful.",
    "Without a doubt.",
    "Yes.",
    "Yes – definitely.",
    "You may rely on it.",
]
"""8ball messages."""
langs = [
    "af",
    "ga",
    "sq",
    "it",
    "ar",
    "ja",
    "az",
    "kn",
    "eu",
    "ko",
    "bn",
    "la",
    "be",
    "lv",
    "bg",
    "lt",
    "ca",
    "mk",
    "ms",
    "mt",
    "hr",
    "no",
    "cs",
    "fa",
    "da",
    "pl",
    "nl",
    "pt",
    "en",
    "ro",
    "eo",
    "ru",
    "et",
    "sr",
    "tl",
    "sk",
    "fi",
    "sl",
    "fr",
    "es",
    "gl",
    "sw",
    "ka",
    "sv",
    "de",
    "ta",
    "el",
    "te",
    "gu",
    "th",
    "ht",
    "tr",
    "iw",
    "uk",
    "hi",
    "ur",
    "hu",
    "vi",
    "is",
    "cy",
    "id",
    "yi",
]
translit_map = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sh'",
    "ы": "y",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}
punto_map = {
    "a": "ф",
    "b": "и",
    "c": "с",
    "d": "в",
    "e": "у",
    "f": "а",
    "g": "п",
    "h": "р",
    "i": "ш",
    "j": "о",
    "k": "л",
    "l": "д",
    "m": "ь",
    "n": "т",
    "o": "щ",
    "p": "з",
    "q": "й",
    "r": "к",
    "s": "ы",
    "t": "е",
    "u": "г",
    "v": "м",
    "w": "ц",
    "x": "ч",
    "y": "н",
    "z": "я",
    ";": "ж",
    "'": "э",
    "`": "ё",
    ",": "б",
    ".": "ю",
}
punto_map_reversed = {v: k for k, v in punto_map.items()}
tr_endpoints = {
    "clients5": {
        "url_template": "https://clients5.google.com/translate_a/t?"
        "client=dict-chrome-ex&sl={0}&tl={1}&dt=t&q={2}",
        "get_lang": lambda _: _["ld_result"]["srclangs"][0],
        "get_text": lambda _: _["sentences"]["trans"],
    },
    "translate": {
        "url_template": "https://translate.googleapis.com/translate_a/"
        "single?client=gtx&sl={0}&tl={1}&dt=t&q={2}",
        "get_lang": lambda _: _[2],
        "get_text": lambda _: "".join(b[0] for b in _[0]),
    },
}
default_chance = 15
simple_replies_collection = {"specific_name": [50, [""]]}
ascii_ascending_luminance = ".,-~:;=!*#$@"

CURR_DIR = Path(__file__).resolve(strict=True).parent
AH_BASE_URL = yarl.URL("https://www.wowauctions.net/auctionHouse")
NORDNAAR_AH_SCRAPER = AHScraper(AH_BASE_URL / "turtle-wow/nordanaar/mergedAh/", CURR_DIR / "twow_items.json")
"""Auction house objects."""


def de_latinize(text):
    """Switch similar latin chars with cyrillic analogues.

    :param str text: input

    :return: normalized text
    """

    chars = {
        "e": "е",
        "t": "т",
        "y": "у",
        "o": "о",
        "p": "р",
        "a": "а",
        "h": "н",
        "k": "к",
        "x": "х",
        "c": "с",
        "b": "в",
        "m": "м",
    }
    for k, v in chars.items():
        text = text.replace(k, v)
    return text


def transform_special_characters(text):
    """Switch complex char sequences with similar chars.

    :param str text: input

    :return: transformed text
    """

    coll = {"}{": "х", "III": "ш", "()": "o"}
    for k, v in coll.items():
        text = text.replace(k, v)
    return text


def normalize_text(
    text, simple_mask=False, do_de_latinize=False, special_chars=False, markdown=False
):
    """Text normalization.

    :param str text: input
    :param bool simple_mask: get rid of varoius characters
    :param bool de_latinize: switch similar characters with its cyrillic counterparts
    :param bool special_chars: switch complex sequences with similar chars
    """

    if simple_mask:
        text = re.sub(
            r"\^|\$|!|#|%|^|&|€|£|¢|¥|§|<|>|\?|~|\*|,|[0-9]|:|;|\[|\]|=|-|\+|_",
            "",
            text.lower(),
        ).replace("ё", "е")
    if do_de_latinize:
        text = de_latinize(text)
    if special_chars:
        text = transform_special_characters(text)
    if markdown:
        text = re.sub(r"\*|_|~|", "", text)
    return text


def translate(text, lang_from=None, lang_to=None, endpoint="translate"):
    """Translate text."""

    text = urllib.parse.quote(text)
    if endpoint and endpoint not in tr_endpoints.keys():
        endpoints = ", ".join(list(tr_endpoints.keys()))
        raise Exception(f"Unsupported endpoint provided. Possible values: {endpoints}")
    tr_toolset = tr_endpoints[endpoint]
    url = tr_toolset["url_template"].format(lang_from or "auto", lang_to or "en", text)
    raw = json.loads(requests.get(url).text)

    return {
        "lang": tr_toolset["get_lang"](raw),
        "text": tr_toolset["get_text"](raw),
    }


def translate_helper(raw_text):
    """Helper for translate(), managing prefix configurations."""

    prefix = raw_text.split()[0]
    text = raw_text[len(prefix) + 1 :]

    if len(prefix) == 2:
        return translate(text)
    elif len(prefix) == 4:
        return translate(text, lang_to=prefix[2:4])
    elif len(prefix) == 6:
        return translate(text, lang_from=prefix[2:4], lang_to=prefix[4:6])
    else:
        raise CommandMalformed(f"Received invalid translation command '{raw_text}'")


def mangle(text, resulting_lang="ru", hops=4):
    """Scrambles text by consequently translating through multiple random languages."""

    max_len = 800
    if len(text) > max_len:
        raise Exception(f"Text is too long! (>{max_len}):\n{text}")

    lang_from = "auto"
    lang_set = set(langs).difference(["ru"])
    lang_sequence = random.sample(lang_set, k=hops) + [resulting_lang]

    for l in lang_sequence:
        translated = translate(text, lang_from=lang_from, lang_to=l)
        lang_from = l
        text = translated["text"]
        time.sleep(0.12)

    return text


def starify(sentence, limit=600):
    """Write on a night sky."""

    alphabet = " " * 50 + "★★●°°☾☆¸¸¸,..:'"
    excluded = " "
    words = sentence.split(" ")

    for i in range(len(words)):
        if i == 0:
            words[i] = f" {words[i]}.. "
        elif i == len(words) - 1:
            words[i] = f" ...{words[i]} "
        else:
            words[i] = f" ..{words[i]}.. "

    limit = limit - sum([len(w) for w in words])
    payload = words
    points = [int(limit * (i + 1) / (len(payload) + 1)) for i in range(len(payload))]
    payload = list(zip(points, payload))
    sky = ""
    last_char = None

    for _ in range(limit):
        if len(sky) in points:
            sky += next(word for point, word in payload if point == len(sky))
        if last_char is None or last_char in excluded:
            last_char = random.choice(alphabet)
        else:
            last_char = random.choice(alphabet.replace(last_char, ""))
        sky += last_char

    return sky


def roll(roll_indices: list[str]):
    """Roll dice."""

    dice_limit = 10**30

    def get_rolls(s):
        if "-" in s:
            left, right = (int(value) for value in re.split(r"-", s))
            if left > dice_limit or right > dice_limit:
                raise Exception("range value(s) are too high")
            return (f"{left}-{right}:", [random.randint(left, right)])
        else:
            roll_params = re.split(r"d", s if "d" in s else f"d{s}")
            throws = 1 if roll_params[0] == "" else int(roll_params[0])
            sides = int(roll_params[1])
            if sides == 0:
                raise Exception("wrong arg")
            if throws > 100 or sides > dice_limit:
                raise Exception("dice size/throw count is too high")

            return (
                f"{throws}d{sides}:",
                [random.randint(1, sides) for _ in range(throws)],
            )

    rolls = [get_rolls(_) for _ in roll_indices]
    text = None

    if len(rolls) == 1 and len(rolls[0][1]) == 1:
        text = f"rolls: {rolls[0][1][0]}"
    else:
        text = "rolls:\n"
        total = 0
        for label, value in rolls:
            text += f"{label} {', '.join([str(_) for _ in value])}\n"
            total += sum(value)
        text += f"---\ntotal: {total}"

    return text


def slot_sequence(emojis, slots=3, seq_len=8):
    """Produce a sequence of slot states in string format.

    :param str emojis:
    """

    if len(emojis) < slots:
        raise Exception(f"Not enough static emojis ({len(emojis)}).")

    emojis = [format_emoji(e) for e in emojis]
    sample = [emojis.pop(emojis.index(random.choice(emojis))) for _ in range(slots)]
    sequence = [
        " ".join(random.choice(sample) for slot in range(slots)) for seq in range(seq_len)
    ]
    success = sequence[-1].count(sequence[-1].split()[0]) == slots

    return sequence, success


def ask_8ball():
    """Fetch random 8ball message."""

    return random.choice(ICOSAHEDRON)


def format_emoji(emoji):
    """Format emojis so they render properly once sent."""

    return f"<:{emoji.name}:{emoji.id}>"


def format_user(user):
    """Proper user format for chat."""

    return f"<@{user.id}>"


def wiki_summary(query):
    """Extract first available wiki summary on provided query.

    :param str query: wiki query
    """

    uri = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
    try:
        req = json.loads(requests.get(uri).text)
        return (
            f"{req['title']}:\n{req['extract']}\n"
            f"({req['content_urls']['desktop']['page']})"
        )
    except KeyError:
        raise CommandExecutionError()


def urban_query(token, query):
    """Extract overall urban dictionary definitions

    :param str query: term, phrase

    :return: query definition
    """

    headers = {
        "x-rapidapi-host": "mashape-community-urban-dictionary.p.rapidapi.com",
        "x-rapidapi-key": token,
    }
    params = {"term": urllib.parse.quote(query)}
    request = requests.get(
        "https://mashape-community-urban-dictionary.p.rapidapi.com/define",
        headers=headers,
        params=params,
    )
    res = json.loads(request.text)

    if len(res["list"]):
        descr = res["list"][0]
        mask = r"\[|\]"
        return (
            descr["word"],
            re.sub(mask, "", descr["definition"]),
            re.sub(mask, "", descr["example"]),
            descr["permalink"],
        )

    return None


def doc(text):
    """Eliza psychotherapist hotline."""

    # TODO: add dialog buffer support
    return nltk.chat.eliza.eliza_chatbot.respond(text)


def is_morse(text):
    """Evaluate if provided text is morse code."""

    chars = {}

    for char in text:
        chars[char] = chars[char] + 1 if char in chars else 1
        if char not in [".", "-", " "] or len(chars) > 3:
            return False

    return True


def from_morse(text):
    """Convert morse code to text."""

    if not isinstance(text, str):
        raise CommandMalformed()

    words = text.split("  ") if "  " in text else [text]
    words_translated = []
    morse_map = MORSE_CODE.items()

    for word in (w.strip() for w in words):
        if word:
            words_translated.append(
                "".join(
                    next((k for k, v in morse_map if v == char), "")
                    for char in word.split()
                )
            )

    return " ".join(words_translated)


def to_morse(text):
    """Convert text to morse code."""

    return " ".join(MORSE_CODE[_] for _ in text)


def morse_helper(text):
    """Helper method for morse code translation."""

    if is_morse(text):
        return from_morse(text)
    else:
        return to_morse(text)


def punto(text):
    """Attempt to punto switch provided text."""

    keys = set(text)
    latin_count = len([char for char in keys if char in punto_map])
    cyrillic_count = len([char for char in keys if char in punto_map_reversed])
    use_map = punto_map if latin_count >= cyrillic_count else punto_map_reversed

    return "".join(use_map.get(char, char) for char in text)


def translitify(text):
    """Attempt to convert content into gibberish translit."""

    return "".join([translit_map.get(char) or char for char in text])


def resource_usage(text):
    """Returns host system resource usage."""

    def mem_summary(resource):
        return (
            f"{round(resource.percent, 1)}% "
            f"({round(resource.used / BYTES_GB, 2)}GB/"
            f"{round(resource.total / BYTES_GB, 2)}GB)"
        )

    cpu_avg = psutil.getloadavg()[-1] / psutil.cpu_count() * 100
    return (
        f"{socket.gethostname()}:\n"
        f"CPU: {round(cpu_avg, 1)}% ({os.cpu_count()} cores)\n"
        f"RAM: {mem_summary(psutil.virtual_memory())}\n"
        f"swap: {mem_summary(psutil.swap_memory())}\n"
        f"disk: {mem_summary(psutil.disk_usage('/'))}"
    )


def ah_query(text: str) -> str:
    """Fetch AH prices for items specified in text."""

    return NORDNAAR_AH_SCRAPER.format_item_prices(NORDNAAR_AH_SCRAPER.fetch_prices(text))
