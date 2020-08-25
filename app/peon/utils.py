"""Various utils, DB operations, etc."""

import binascii
import json
import os
import random
import re
import requests
import string
import traceback
import urllib.parse


ENV_TOKEN = "token"
ENV_RAPIDAPI_TOKEN = "rapidapi_token"
ENV_DB_HOST = "MONGO_HOST"
ENV_DB_PORT = "MONGO_PORT"
ENV_DB_USER = "MONGO_INITDB_ROOT_USERNAME"
ENV_DB_PASS = "MONGO_INITDB_ROOT_PASSWORD"
ENV_VARS = [
    ENV_TOKEN,
    ENV_RAPIDAPI_TOKEN,
    ENV_DB_HOST,
    ENV_DB_PORT,
    ENV_DB_USER,
    ENV_DB_PASS,
]
"""Required environment variables."""


ASSETS_FOLDER = "/app/assets"

MORSE_CODE = {
    "a":".-", "b":"-...", "c":"-.-.", "d":"-..", "e":".", "f":"..-.", "g":"--.",
    "h":"....", "i":"..", "j":".---", "k":"-.-", "l":".-..", "m":"--", "n":"-.",
    "o":"---", "p":".--.", "q":"--.-", "r":".-.", "s":"...", "t":"-", "u":"..-",
    "v":"...-", "w":".--", "x":"-..-", "y":"-.--", "z":"--..",
    "1":".----", "2":"..---", "3":"...--", "4":"....-", "5":".....",
    "6":"-....", "7":"--...", "8":"---..", "9":"----.", "0":"-----",
    ", ":"--..--", ".":".-.-.-", "?":"..--..", "/":"-..-.", "-":"-....-",
    "(":"-.--.", ")":"-.--.-", " ": " ",
}
"""Morse code dictionary."""


def get_env_vars():
    """
    Check if required environment variables are
    set and return dict containing them.
    """

    missing_variables = [_ for _ in ENV_VARS if _ not in os.environ.keys()]
    if len(missing_variables) > 0:
        raise Exception("Error: missing required variables: %s" % missing_variables)

    return {key: os.environ[key] for key in ENV_VARS}


def get_file(name, mode="rb"):
    """Returns existing file as bytes."""

    return open("{0}/{1}".format(ASSETS_FOLDER, name), mode).read()


# ------ NOTE: temporary entities (awaiting db implementation)
langs = ["af", "ga", "sq", "it", "ar", "ja", "az", "kn", "eu", "ko", "bn", "la",
         "be", "lv", "bg", "lt", "ca", "mk", "ms", "mt", "hr", "no", "cs", "fa",
         "da", "pl", "nl", "pt", "en", "ro", "eo", "ru", "et", "sr", "tl", "sk",
         "fi", "sl", "fr", "es", "gl", "sw", "ka", "sv", "de", "ta", "el", "te",
         "gu", "th", "ht", "tr", "iw", "uk", "hi", "ur", "hu", "vi", "is", "cy",
         "id", "yi"]
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
d = lambda _: binascii.a2b_hex(_).decode('utf8')
default_chance = 15
simple_replies_collection = {
    'саня': [50, [d(b'd185d183d0b920d181d0bed181d0b8'), 'ты в порядке?']],
    'леха': [33, [d(b'd0b3d0bed0b2d0bdd0b020d0bbd0b5d0bfd0b5d185d0b0')]],
    d(b'd181d0bbd0b0d0b2d0b0d183d0bad180d0b0d0b8d0bdd0b5'): [
        100, [d(b'd093d0b5d180d0bed18fd0bc20d181d0bbd0b0d0b2d0b021')]
    ],
    'дрон': [5, [d(b'd0b020d0b4d180d0bed0bd20d185d0bed180d0bed188d0b8d0b9')]],
    'тарас': [20, [
        d(b'd0b020d0b2d0bed18220d0b820d0bdd0b520d0bfd0b8d0b4d0bed180d0b0d181'),
        d(b'd0b2d181d0b52dd182d0b0d0bad0b820d0bfd0b8d0b4d0b0d180d0b0d181')]
    ],
    'сандра': [default_chance,
               [d(b'd187d0b5d188d0b5d18220d092d0b5d189d0bad0b5d0bfd0b5d0bad0b0')]],
    'сандрес': [default_chance, ['европейский конгресс']],
    'алексей': [33, [d(b'd0b5d0b1d0b5d18220d0b3d183d181d0b5d0b9')]],
    'алеша': [default_chance,
              [d(b'd0b220d188d182d0b0d0bdd0b0d18520d0b4d180d0b0d0bad0bed188d0b0')]],
    'коля': [default_chance, [d(b'd0b5d0b1d0b5d182d181d18f20d0b220d0bfd0bed0bbd0b5')]],
    'жекич': [default_chance, [d(b'd0bbd0bed0b2d0b8d18220d180d0b6d0b5d0bad0b8d187')]],
}
role_emergency = "<@&453948742710722569>"
role_emergency_raw = "453948742710722569"
emergency_phrases = [
    'а ну-ка забил слотецки', '-> слот забил',
    'пересмотр зовет', 'к барьеру!',
    d(b'd0b7d0b0d0b8d0b1d0b0d0b22c20d0b3d0be21'),
    'мерси вызывает!', 'the world could always use more heroes!',
    'gwa-gwa-gwa!! gwa!', 'bootywatch awaits',
    'аляяяяярм', 'поехали!', 'запрыгивай, а то станешь саней',
    'заходи. или ты коля?',
    'slish, sel na motor i plusanul! :pig: :dark_sunglasses: ',
]
rolling_alexeys = [d(b'616c6568614562616c6f'), d(b'6562616c6f416c656861')]
slot_grats = [
    d(b'7b307d2c20d0b020d182d18b20d0bdd0b5d0bfd0bbd0bed185'),
    d(b'd09dd18320d0b2d181d1912c20d182d0b5d0bfd0b5d180d18c20d0b2d181d0b520d182'
        b'd191d0bbd0bad0b820d182d0b2d0bed0b8'),
    d(b'd09bd183d187d188d0b520d0b1d18b20d182d18b20d182d0b0d0ba20d0b7d0b020d0be'
        b'd0b1d0b6d0b5d0bad182d0b8d0b220d0b1d0b8d0bbd181d18f'),
    d(b'd09ad180d0b0d181d0b8d0b2d0be20d0bad180d183d182d0b8d188d18c2c207b307d21'),
    d(b'7b307d202d20d0bfd0bed0b1d0b5d0b4d0b8d182d0b5d0bbd18c20d0bfd0be20d0b6d0'
        b'b8d0b7d0bdd0b8'),
    d(b'28d18f20d0bdd0b8d187d0b5d0b3d0be20d0bdd0b520d0bfd0bed0b4d0bad180d183d1'
        b'87d0b8d0b2d0b0d0bb2c203130302520d0b8d0bdd184d0b029'),
    d(b'd0a1d0b5d0bad182d0bed18020d0bfd180d0b8d0b720d0bdd0b020d0b1d0b0d180d0b0'
        b'd0b1d0b0d0bdd0b521'),
]
generic_grats = [
    "Congratulations!", "wow, unbelievable", "Once in a lifetime achievement!",
    "Incredible!", "Absolutely gorgeous outcome!", "Well done!"
]
ascii_ascending_luminance = ".,-~:;=!*#$@"
# ------

def de_latinize(text):
    """Switch similar latin chars with cyrillic analogues.

    :param str text: input

    :return: normalized text
    """

    chars = {'e': 'е', 't': 'т', 'y': 'у', 'o': 'о', 'p': 'р', 'a': 'а',
            'h': 'н', 'k': 'к', 'x': 'х', 'c': 'с', 'b': 'в', 'm': 'м'}
    for k, v in chars.items():
        text = text.replace(k, v)
    return text


def transform_special_characters(text):
    """Switch complex char sequences with similar chars.

    :param str text: input

    :return: transformed text
    """

    coll = {'}{': 'х', 'III': 'ш', '()': 'o'}
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
            r'\^|\$|!|#|%|^|&|€|£|¢|¥|§|<|>|\?|~|\*|,|[0-9]|:|;|\[|\]|=|-|\+|_',
            '', text.lower()).replace('ё', 'е')
    if do_de_latinize:
        text = de_latinize(text)
    if special_chars:
        text = transform_special_characters(text)
    if markdown:
        text = re.sub(r"\*|_|~|", "", text)
    return text


def translate(text, lang_from=None, lang_to=None, endpoint="translate"):
    """Translator."""

    text = urllib.parse.quote(text)
    lang_from = lang_from or "auto"
    lang_to = lang_to or "ru"
    if endpoint and endpoint not in tr_endpoints.keys():
        raise Exception(
            "Unsupported endpoint provided. Possible values: {0}".format(
                ", ".join(list(tr_endpoints.keys()))))
    tr_toolset = tr_endpoints[endpoint]
    url = tr_toolset["url_template"].format(lang_from, lang_to, text)
    raw = json.loads(requests.get(url).text)

    return {
        "lang": tr_toolset["get_lang"](raw),
        "text": tr_toolset["get_text"](raw),
    }


def starify(sentence, limit=600):
    """Write on a night sky."""

    alphabet = " " * 50 + "★★●°°☾☆¸¸¸,..:'"
    excluded = " "
    words = sentence.split(" ")

    for i in range(len(words)):
        if i == 0:
            words[i] = " %s.. " % words[i]
        elif i == len(words) - 1:
            words[i] = " ...%s " % words[i]
        else:
            words[i] = " ..%s.. " % words[i]

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
            last_char = random.choice(alphabet.replace(last_char, ''))
        sky += last_char

    return sky


def roll(raw):
    """Roll dice.

    :param str raw: list of raw roll inputs

    :return: roll results
    """

    dice_limit = 10 ** 30

    def get_rolls(s):
        if "-" in s:
            left, right = (int(value) for value in re.split(r'-', s))
            if left > dice_limit or right > dice_limit:
                raise Exception("range value(s) are too high")
            return ("{0}-{1}:".format(left, right), [random.randint(left, right)])
        else:
            roll_params = re.split(r'd', s if "d" in s else "d{0}".format(s))
            throws = 1 if roll_params[0] == '' else int(roll_params[0])
            sides = int(roll_params[1])
            if sides == 0:
                raise Exception("wrong arg")
            if throws > 100 or sides > dice_limit:
                raise Exception("dice size/throw count is too high")

            return ("{0}d{1}:".format(throws, sides),
                    [random.randint(1, sides) for _ in range(throws)])

    rolls = [get_rolls(_) for _ in raw]
    text = None

    if len(rolls) == 1 and len(rolls[0][1]) == 1:
        text = "rolls: {0}".format(rolls[0][1][0])
    else:
        text = "rolls:\n"
        total = 0
        for label, value in rolls:
            text += "{0} {1}\n".format(label, ', '.join([str(_) for _ in value]))
            total += sum(value)
        text += "---\ntotal: {0}".format(total)

    return text


def slot_sequence(emojis, slots=3, seq_len=8):
    """Produce a sequence of slot states in string format.

    :param str emojis:
    """

    if len(emojis) < slots:
        raise Exception(
            "Not enough static emojis ({0}).".format(len(emojis)))

    emojis = [format_emoji(e) for e in emojis]
    sample = [emojis.pop(emojis.index(random.choice(emojis))) for _ in range(slots)]
    sequence = [" ".join(random.choice(sample) for slot in range(slots))
                for seq in range(seq_len)]
    success = sequence[-1].count(sequence[-1].split()[0]) == slots

    return sequence, success


def format_emoji(emoji):
    """Format emojis so they render properly once sent."""

    return "<:{0.name}:{0.id}>".format(emoji)


def format_user(user):
    """Proper user format for chat."""

    return "<@{0}>".format(user.id)


def wiki_summary(query):
    """Extract first available wiki summary on provided query.

    :param str query: wiki query
    """

    req = json.loads(requests.get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/{0}".format(
            urllib.parse.quote(query))).text)

    return "{0}:\n{1}\n({2})".format(
        req["title"], req["extract"], req["content_urls"]["desktop"]["page"])


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
        mask = r'\[|\]'
        return (descr["word"], re.sub(mask, '', descr["definition"]),
                re.sub(mask, '', descr["example"]), descr["permalink"])
    else:
        return None


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

    words = text.split("  ") if "  " in text else [text]
    words_translated = []

    for word in (w.strip() for w in words):
        if word:
            words_translated.append(
                "".join(next(k for k, v in MORSE_CODE.items() if v == char)
                        for char in word.split()))

    return " ".join(words_translated)


def to_morse(text):
    """Convert text to morse code."""

    return " ".join(MORSE_CODE[_] for _ in text)
