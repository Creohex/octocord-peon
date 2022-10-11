"""Various utils, DB operations, etc."""

import binascii
import json
import os
import random
import re
import requests
import time
import urllib.parse

import nltk.chat.eliza
import steamapi

from peon_common import exceptions


ENV_TOKEN_DISCORD = "discord_token"
ENV_TOKEN_TELEGRAM = "telegram_token"
ENV_TOKEN_RAPIDAPI = "rapidapi_token"
ENV_TOKEN_STEAMAPI = "steamapi_token"
ENV_TWITCH_CLIENT_ID = "twitch_client_id"
ENV_TWITCH_CLIENT_SECRET = "twitch_client_secret"
ENV_DB_ENABLED = "DB_ENABLED"
ENV_DB_HOST = "MONGO_HOST"
ENV_DB_PORT = "MONGO_PORT"
ENV_DB_USER = "MONGO_INITDB_ROOT_USERNAME"
ENV_DB_PASS = "MONGO_INITDB_ROOT_PASSWORD"
ENV_VARS = [
    ENV_TOKEN_DISCORD,
    ENV_TOKEN_TELEGRAM,
    ENV_TOKEN_RAPIDAPI,
    ENV_TOKEN_STEAMAPI,
    ENV_TWITCH_CLIENT_ID,
    ENV_TWITCH_CLIENT_SECRET,
    ENV_DB_ENABLED,
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


def get_env_vars():
    """Check if required env vars are set and return dict containing them."""

    missing_variables = [_ for _ in ENV_VARS if _ not in os.environ.keys()]
    if len(missing_variables) > 0:
        raise Exception("Error: missing required variables: %s" % missing_variables)

    return {key: os.environ[key] for key in ENV_VARS}


def get_file(name, mode="rb"):
    """Returns existing file as bytes."""

    return open(f"{ASSETS_FOLDER}/{name}", mode).read()


langs = ["af", "ga", "sq", "it", "ar", "ja", "az", "kn", "eu", "ko", "bn", "la",
         "be", "lv", "bg", "lt", "ca", "mk", "ms", "mt", "hr", "no", "cs", "fa",
         "da", "pl", "nl", "pt", "en", "ro", "eo", "ru", "et", "sr", "tl", "sk",
         "fi", "sl", "fr", "es", "gl", "sw", "ka", "sv", "de", "ta", "el", "te",
         "gu", "th", "ht", "tr", "iw", "uk", "hi", "ur", "hu", "vi", "is", "cy",
         "id", "yi"]
translit_map = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sh'", "ы": "y", "э": "e", "ю": "yu", "я": "ya",
}
punto_map = {
    "a": "ф", "b": "и", "c": "с", "d": "в", "e": "у", "f": "а", "g": "п",
    "h": "р", "i": "ш", "j": "о", "k": "л", "l": "д", "m": "ь", "n": "т",
    "o": "щ", "p": "з", "q": "й", "r": "к", "s": "ы", "t": "е", "u": "г",
    "v": "м", "w": "ц", "x": "ч", "y": "н", "z": "я", ";": "ж", "'": "э",
    "`": "ё", ",": "б", ".": "ю",
}
punto_map_reversed = {v: k for k,v in punto_map.items()}
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
steam_users = {
    "creohex": {"userid": 76561198044030521},
    "fringe": {"userid": 76561198060131971},
    "gorelka": {"userurl": "PIZERok"},
    "dronxd": {"userid": 76561198017345589},
    "dakorher": {"userurl": "Dakorher"},
    "ankarnamir": {"userid": 76561198011087208},
    "dees": {"userid": 76561198011748348},
    "sashoker": {"userurl": "Sashoker"},
}
steam_commands_mapping = {
    "id": lambda user: user.id,
    "name": lambda user: user.real_name,
    "profile": lambda user: user.profile_url,
    "fiend_count": lambda user: len(user.friends),
    "friends": lambda user: ", ".join(friend.name for friend in user.friends),
    "avatar": lambda user: user.avatar_medium,
    "avatar_big": lambda user: user.avatar_full,
    "last_online": lambda user: user.last_logoff,
    "level": lambda user: user.level,
    "currently_playing": lambda user: user.currently_playing,
    "game_count": lambda user: len(user.games),
    "owned_game_count": lambda user: len(user.owned_games),
    "vac": lambda user: str(user.is_vac_banned),
    "game_bans": lambda user: user.number_of_vac_bans,
}
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
    """Translate text."""

    text = urllib.parse.quote(text)
    if endpoint and endpoint not in tr_endpoints.keys():
        endpoints = ", ".join(list(tr_endpoints.keys()))
        raise Exception(f"Unsupported endpoint provided. Possible values: {endpoints}")
    tr_toolset = tr_endpoints[endpoint]
    url = tr_toolset["url_template"].format(lang_from or "auto",
                                            lang_to or "ru",
                                            text)
    raw = json.loads(requests.get(url).text)

    return {
        "lang": tr_toolset["get_lang"](raw),
        "text": tr_toolset["get_text"](raw),
    }


def translate_helper(raw_text):
    """Helper for translate(), managing prefix configurations."""

    prefix = raw_text.split()[0]
    text = raw_text[len(prefix)+1:]

    if len(prefix) == 2:
        return translate(text)
    elif len(prefix) == 4:
        return translate(text, lang_to=prefix[2:4])
    elif len(prefix) == 6:
        return translate(text, lang_from=prefix[2:4], lang_to=prefix[4:6])
    else:
        raise exceptions.CommandMalformed(
            f"Received invalid translation command '{raw_text}'")


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


def roll(roll_indices: list[str]):
    """Roll dice."""

    dice_limit = 10 ** 30

    def get_rolls(s):
        if "-" in s:
            left, right = (int(value) for value in re.split(r'-', s))
            if left > dice_limit or right > dice_limit:
                raise Exception("range value(s) are too high")
            return (f"{left}-{right}:", [random.randint(left, right)])
        else:
            roll_params = re.split(r'd', s if "d" in s else f"d{s}")
            throws = 1 if roll_params[0] == '' else int(roll_params[0])
            sides = int(roll_params[1])
            if sides == 0:
                raise Exception("wrong arg")
            if throws > 100 or sides > dice_limit:
                raise Exception("dice size/throw count is too high")

            return (f"{throws}d{sides}:",
                    [random.randint(1, sides) for _ in range(throws)])

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
    sequence = [" ".join(random.choice(sample) for slot in range(slots))
                for seq in range(seq_len)]
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
        return (f"{req['title']}:\n{req['extract']}\n"
                f"({req['content_urls']['desktop']['page']})")
    except KeyError:
        raise exceptions.CommandExecutionError()


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

    return None


def steam(query):
    """Steam API integration."""

    if not re.match(r"^\w+\s\w+", query):
        raise exceptions.CommandMalformed("expecting: '<user> <command> <_args>'")

    user_name, cmd, *_ = query.split()

    user_id = steam_users.get(user_name, None)
    steamapi.core.APIConnection(api_key=os.environ.get(ENV_TOKEN_STEAMAPI),
                                validate_key=True)

    if user_id:
        user = steamapi.user.SteamUser(**user_id)
    else:
        try:
            try:
                user_id = {"userid": int(user_name)}
            except ValueError:
                user_id = {"userurl": user_name}

            user = steamapi.user.SteamUser(**user_id)
        except steamapi.errors.UserNotFoundError:
            raise exceptions.CommandExecutionError(f"user '{user_name}' not found.")

    cmd_handler = steam_commands_mapping.get(cmd, None)
    if cmd_handler is None:
        raise exceptions.CommandMalformed(
            f"Supported commands: {', '.join(steam_commands_mapping.keys())}")

    return cmd_handler(user)


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
