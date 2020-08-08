"""Various utils, DB operations, etc."""

import binascii
import json
import os
import random
import re
import requests
import urllib.parse

from pymongo import MongoClient


ENV_TOKEN = "token"
ENV_RAPIDAPI_TOKEN = "rapidapi_token"
ENV_DB_HOST = "db_host"
ENV_DB_DB = "db_db"
ENV_DB_USER = "db_user"
ENV_DB_PASS = "db_pass"
ENV_DB_PORT = "db_port"
ENV_VARS = [
    ENV_TOKEN,
    ENV_RAPIDAPI_TOKEN,
    ENV_DB_HOST,
    ENV_DB_DB,
    ENV_DB_USER,
    ENV_DB_PASS,
    ENV_DB_PORT,
]
"""Required environment variables."""


def get_env_vars():
    """
    Check if required environment variables are
    set and return dict containing them.
    """

    missing_variables = [_ for _ in ENV_VARS if _ not in os.environ.keys()]
    if len(missing_variables) > 0:
        raise Exception("Error: missing required variables: %s" % missing_variables)

    return {key: os.environ[key] for key in ENV_VARS}


class Mongo():
    """Mongo operations."""

    @property
    def client(self):
        return self.client

    @property
    def env_vars(self):
        if not self._env_vars:
            self._env_vars = get_env_vars()

        return self._env_vars

    def __init__(self):
        self._env_vars = None
        self.client = MongoClient(self.env_vars[ENV_DB_HOST], self.env_vars[ENV_DB_PORT])


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
simple_replies_collection = {"specific_name": [50, [""]]}
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
peon_commands = [
    "!stats\t - show bot stats",
    "!roll 2d8 + d12\t - roll dice",
    "!roll L5\t - roll aleha",
    "!tr blabla\t - translate",
    "!starify blabla\t - write mystical stuff on night sky",
    "!slot\t - test your luck",
    "!wiki\t - find out about stuff",
    "!urban\t - lookup outdated meme terms on urban dictionary",
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
