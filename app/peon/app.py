import binascii
import json
import os
import random
import re
import requests
import time
import urllib.parse

import discord
import pymysql


class Utils():

    @staticmethod
    def get_env_vars():
        """
        Check if required environment variables are
        set and return dict containing them.
        """

        required_variables = [
            'token',
            'db_host',
            'db_username',
            'db_password',
        ]
        missing_variables = [_ for _ in required_variables if _ not in os.environ.keys()]
        if len(missing_variables) > 0:
            raise Exception("Error: missing required variables: %s" % missing_variables)

        return {
            "db_host": os.environ['db_host'],
            "db_db": 'octocord',
            "db_user": os.environ['db_username'],
            "db_pass": os.environ['db_password'],
            "token": os.environ['token'],
        }


class Peon():

    # NOTE: temporary entities (awaiting db implementation)
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
        d(b'd181d0bbd0b0d0b2d0b0d183d0bad180d0b0d0b8d0bdd0b5'):
            [100, [d(b'd093d0b5d180d0bed18fd0bc20d181d0bbd0b0d0b2d0b021')]],
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
    peon_commands = [
        "!stats\t - show bot stats",
        "!roll 2d8 + d12\t - roll dice",
        "!roll L5\t - roll aleha",
        "!tr blabla\t - translate",
        "!starify blabla\t - write mystical stuff on night sky",
        "!slot\t - test your luck",
        "!wiki\t - find out about stuff",
    ]
    rolling_alexeys = [d(b'616c6568614562616c6f'), d(b'6562616c6f416c656861')]
    slot_blacklist = [
        "clap", "hmm", "pepek", "loading", "lookrocknroll", "alehaSpin", "dansU"]
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

    @classmethod
    def de_latinize(cls, text):
        """Switch similar latin chars with cyrillic analogues.

        :param str text: input

        :return: normalized text
        """

        chars = {'e': 'е', 't': 'т', 'y': 'у', 'o': 'о', 'p': 'р', 'a': 'а',
                'h': 'н', 'k': 'к', 'x': 'х', 'c': 'с', 'b': 'в', 'm': 'м'}
        for k, v in chars.items():
            text = text.replace(k, v)
        return text

    @classmethod
    def transform_special_characters(cls, text):
        """Switch complex char sequences with similar chars.

        :param str text: input

        :return: transformed text
        """

        coll = {'}{': 'х', 'III': 'ш', '()': 'o'}
        for k, v in coll.items():
            text = text.replace(k, v)
        return text

    @classmethod
    def normalize_text(
        cls, text, simple_mask=True, de_latinize=True, special_chars=True
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
        if de_latinize:
            text = cls.de_latinize(text)
        if special_chars:
            text = cls.transform_special_characters(text)
        return text

    @classmethod
    def translate(cls, text, lang_from=None, lang_to=None, endpoint="translate"):
        """Translator."""

        text = urllib.parse.quote(text)
        lang_from = lang_from or "auto"
        lang_to = lang_to or "ru"
        if endpoint and endpoint not in cls.tr_endpoints.keys():
            raise Exception(
                "Unsupported endpoint provided. Possible values: {0}".format(
                    ", ".join(list(cls.tr_endpoints.keys()))))
        tr_toolset = cls.tr_endpoints[endpoint]
        url = tr_toolset["url_template"].format(lang_from, lang_to, text)
        raw = json.loads(requests.get(url).text)

        return {
            "lang": tr_toolset["get_lang"](raw),
            "text": tr_toolset["get_text"](raw),
        }

    @classmethod
    def starify(cls, sentence, limit=600):
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

    @classmethod
    def roll(cls, raw):
        """Roll dice.

        :param str raw: raw input string

        :return: roll results
        """

        def get_rolls(s):
            raw = re.split(r'd', s)
            n = 1 if raw[0] == '' else int(raw[0])
            size = int(raw[1])
            if size == 0:
                raise Exception("wrong arg")
            return (n, size, [random.randint(1, size) for _ in range(n)])

        rolls = [get_rolls(_) for _ in raw]
        text = None

        if len(rolls) == 1 and rolls[0][0] == 1:
            text = "rolls: {0}".format(rolls[0][2][0])
        else:
            text = "rolls:\n"
            total = 0
            for r in rolls:
                text += "{0}d{1}: {2}\n".format(
                    r[0], r[1], ', '.join([str(_) for _ in r[2]]))
                total += sum(r[2])
            text += "---\ntotal: {0}".format(total)

        return text

    @classmethod
    def slot_sequence(cls, emojis, slots=3, seq_len=8):
        """Produce a sequence of slot states in string format.

        :param str emojis:
        """

        if len(emojis) < slots:
            raise Exception(
                "Not enough emojis.\n({0})".format(cls.format_emojis(emojis)))
        emojis = cls.format_emojis(e for e in emojis if e.name not in cls.slot_blacklist)
        sample = [emojis.pop(emojis.index(random.choice(emojis))) for _ in range(slots)]
        sequence = [" ".join(random.choice(sample)
                             for slot in range(slots))
                    for seq in range(seq_len)]
        success = sequence[-1].count(sequence[-1].split()[0]) == 3

        return sequence, success

    @staticmethod
    def format_emojis(emojis):
        """Format emojis so they render properly once sent."""

        return ["<:{0.name}:{0.id}>".format(e) for e in emojis]

    @staticmethod
    def format_user(user):
        """Proper user format for chat."""

        return "<@{0}>".format(user.id)

    @classmethod
    def wiki_summary(cls, query):
        """Extract first available wiki summary on provided query.

        :param str query: wiki query
        """

        req = json.loads(requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/{0}".format(
                urllib.parse.quote(query))).text)

        return "{0}:\n{1}\n({2})".format(
            req["title"], req["extract"], req["content_urls"]["desktop"]["page"])

    def __init__(self):
        self.env_vars = Utils.get_env_vars()

    def run(self):
        """Run peon."""

        client = discord.Client(messages=3000)

        @client.event
        async def on_ready():
            print('Logged in as')
            print(client.user.name)
            print(client.user.id)
            print('------')

        @client.event
        async def on_message(message):
            if message.author == client.user:
                return

            msg_triggered = False

            async def reply(text, single_reply=False):
                if not single_reply or (single_reply and not msg_triggered):
                    msg_triggered = True
                    return await client.send_message(message.channel, text)

            async def handle_simple_replies():
                payload = self.normalize_text(message.content, special_chars=False)
                for k, v in self.simple_replies_collection.items():
                    if k in payload:
                        chance, phrases = v
                        if len(phrases) > 0 and chance >= random.randint(0, 100):
                            return await reply(random.choice(phrases))

            async def handle_emergency_party_mention():
                if self.role_emergency in message.content:
                    # get all members of this role
                    members = []
                    for m in message.channel.server.members:
                        for r in m.roles:
                            if r.id == self.role_emergency_raw:
                                members.append(m)

                    if len(members) == 0:
                        return False

                    # mention him and write something
                    return await reply('{0} {1}'.format(
                        random.choice(members).mention,
                        random.choice(self.emergency_phrases))
                    )

            # !peon
            if message.content.lower().startswith('!peon'):
                return await reply(
                    'Available commands:\n{0}'.format('\n'.join(self.peon_commands)))

            # !test
            if message.content.startswith('!test'):
                return

            # !tr
            if message.content.startswith('!tr'):
                prefix = message.content.split()[0]
                text = message.content[len(prefix)+1:]
                result = ""

                if len(prefix) == 3:
                    result = self.translate(text)
                elif len(prefix) == 5:
                    result = self.translate(text, lang_to=prefix[3:5])
                elif len(prefix) == 7:
                    result = self.translate(text, lang_from=prefix[3:5],
                                                  lang_to=prefix[5:7])
                else:
                    return await reply(
                        "Correct format: !tr <text..> | !tr<lang_to> <text..> |"
                        " !tr<lang_from><lang_to> <text..>\n(lang = en|es|fi|ru|...)"
                    )

                return await reply("({0}) {1}".format(result["lang"], result["text"]))

            # !stats
            if message.content.startswith('!stats'):
                text = (
                    "bot: {0} / {1}\nconnected servers: {2}\ncurrent channel: {3}s\n"
                    "current db host: {4} ({5})".format(
                        client.user.name,
                        client.user.id,
                        ', '.join(['{0}\n({1})'.format(
                            _.name, str([c.name for c in _.channels]))
                            for _ in client.servers]),
                        str(message.channel),
                        self.env_vars["db_host"],
                        self.env_vars["db_user"])
                )
                return await reply(text)

            # !roll
            if message.content.startswith("!roll "):
                text = message.content
                raw = re.split(r' ?\+ ?', re.split(r'!roll ', text)[1])
                if not len(raw):
                    return

                if "l" in raw[0].lower():
                    real_alexeys = self.format_emojis(filter(
                        lambda e: e.name in self.rolling_alexeys,
                        message.channel.server.emojis))
                    text = " ".join(
                        [real_alexeys[_ % 2]
                         for _ in range(min(int(re.split('l', raw[0].lower())[1]), 200))])
                    await reply(text)
                    await client.delete_message(message)
                else:
                    await reply(self.roll(raw))

                return

            # !starify
            if message.content.startswith("!starify "):
                text = message.content[9:]
                if len(text) > 0:
                    await reply(self.starify(text))
                    await client.delete_message(message)
                return

            # !slot
            if message.content == "!slot":
                sequence, success = self.slot_sequence(message.channel.server.emojis)

                msg = await reply(message.author)
                time.sleep(1)
                for s in sequence:
                    await client.edit_message(msg, s)
                    time.sleep(1)

                await client.add_reaction(msg, emoji="🎊" if success else "😫")

                if success:
                    msg = random.choice(self.slot_grats).format(
                        self.format_user(message.author))
                    if random.choice(range(10)) == 0:
                        congrats = self.translate(
                            random.choice(self.generic_grats),
                            lang_from="en", lang_to=random.choice(self.langs)
                        )["text"]
                        msg += "\n{0}".format(congrats)
                    await reply(msg)

                return

            # !wiki
            if message.content.startswith("!wiki "):
                query = message.content[6:]
                if len(query) > 0:
                    return await reply(self.wiki_summary(query))

            # simple replies
            await handle_simple_replies()

            # @ emergency party handling
            await handle_emergency_party_mention()

            # if message.content.startswith('test'):
            #     await client.edit_message(message, '!!')

        client.run(self.env_vars["token"])
