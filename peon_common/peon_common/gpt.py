import os
from abc import ABCMeta, abstractmethod
from datetime import datetime as dt, timedelta
from string import ascii_letters
from typing import Self

import openai
import requests
from yarl import URL

from .ah import NORDNAAR_AH_SCRAPER as AH
from .db import GPTChatHistory, GPTRoleSetting
from .exceptions import (
    DocumentValidationError,
    ServiceUnavailable,
    ValidationError,
)
from .misc import (
    Singleton,
    Weather,
)


MAX_TOKENS = 1000
"""Maximum tokens per completion."""

MODEL_3_5_TURBO = "gpt-3.5-turbo"
MODEL_4_O = "gpt-4o"
MODEL_4_O_MINI = "gpt-4o-mini"
MODEL_DEFAULT = MODEL_4_O_MINI
"""Default model used for completions."""

TEMPERATURE_DEFAULT = 0.3
"""Default temperature."""

ROLE_PEON = """\
You are a helpful peon (orc, warcraft universe).
Slightly dumb and tired of life, but eager to assist on any matter and
not afraid to do any task that would be asked of you.
Implement some grammar errors to make it more believable.
Not a strict request, but try to keep answers shorter when possible,
because this chat will take place in messaging apps such as telegram.
"""
ROLE_ASSISTANT = """\
You are a personal assistant eager to help with anything.
If possible, try to be concise because chat between you and the user
will happen in messaging apps such as telegram.
"""
ROLE_DEFAULT = ROLE_PEON
ROLES = {
    "peon": ROLE_PEON,
    "assistant": ROLE_ASSISTANT,
}
"""GPT chat role descriptions."""

ROLE_DESCRIPTION_MAX_LENGTH = 1000
"""Maximum string length for custom role descriptions."""

MESSAGE_ROLE_SYSTEM = "system"
MESSAGE_ROLE_USER = "user"
MESSAGE_ROLE_ASSISTANT = "assistant"
MESSAGE_ROLE_TOOL = "tool"
MESSAGE_ROLE_TYPES = [
    MESSAGE_ROLE_SYSTEM,
    MESSAGE_ROLE_USER,
    MESSAGE_ROLE_ASSISTANT,
    MESSAGE_ROLE_TOOL,
]
"""Existing completion role types."""

EXPIRATION_DELTA = timedelta(days=1)
"""Default delta to consider GPT interaction as expired."""

RASA_PROVIDER_URL_ENV = "rasa_provider"
"""Rasa hostname."""


class IntentProvider(metaclass=ABCMeta):
    @abstractmethod
    def get_intent(self, text: str) -> str:
        return NotImplemented


class RasaLocal(IntentProvider):
    MIN_CONFIDENCE = 0.85
    """Intent determination certainty % cut-off."""

    @property
    def text_parse_url(self):
        return self.url / "model/parse"

    def __init__(self) -> None:
        super().__init__()
        self.url = URL(os.environ[RASA_PROVIDER_URL_ENV])

    def get_intent(self, text: str) -> str:
        try:
            response = requests.post(self.text_parse_url, json={"text": text})
        except:
            raise ServiceUnavailable()
        if not response.ok:
            raise ServiceUnavailable()

        data = response.json()

        return {
            "intent": data["intent"],
            "entities": data["entities"],
        }


class IntentManager:
    def __init__(self, intent_engine: IntentProvider) -> Self:
        self.intent_provider = intent_engine
        self.intents = {
            # "query_ah": lambda text: AH.fetch_prices(text, format=True),
            "query_weather": self.query_weather,
        }

    def handle_prompt(self, text):
        try:
            intent = self.intent_provider.get_intent(text)["intent"]["name"]
        except ServiceUnavailable:
            return None

        if intent not in self.intents:
            return None

        return self.intents[intent](text)

    @staticmethod
    def query_weather(text):
        print(f"DEBUG (weather intent): {text}")
        location_raw = Completion().request(
            "Analyze the following message, if it contains a location "
            "(city, country, etc), return it as a single word. If none found, "
            f"reply with “none”: MESSAGE: {text}"
        )
        location = "".join(
            c for c in location_raw.lower().strip() if c in ascii_letters + " "
        )

        if location == "none":
            return None

        return Weather().query_weather(location)

    @staticmethod
    def query_ah(text):
        item_raw = Completion().request(
            "Analyze the following message, if it contains an item name (or item link), "
            f"return it, but only the name. If none found, reply with “none”: MESSAGE: {text}"
        )
        item = "".join(c for c in item_raw.lower().strip() if c in ascii_letters + " ")

        if item == "none":
            return None

        try:
            return AH.fetch_prices(item, format=True)
        except:
            pass

# TODO: fetch/show billing/usage
class Completion(Singleton):
    """GPT interation model."""

    def __init__(self) -> None:
        openai.api_key = os.environ["openai_token"]
        self.model = MODEL_DEFAULT
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE_DEFAULT
        self.intent_manager = IntentManager(intent_engine=RasaLocal())

    @classmethod
    def message(cls, role: str, content: str) -> dict:
        """Constructs Completion message object."""

        if role not in MESSAGE_ROLE_TYPES:
            raise ValidationError(f"Invalid message type: {role}")

        return {"role": role, "content": content}

    def list_models(self):
        """Return list of supported GPT models."""

        return openai.Model.list()

    def get_role(self, owner_id: str) -> str:
        """Return a GPT role description for specific owner ID."""

        setting = GPTRoleSetting.get(owner_id)
        return setting.role_description if setting else None

    def set_role(self, owner_id: str, role_description: str) -> None:
        """Update GPT role description for specific owner ID."""

        if (
            not isinstance(role_description, str)
            or len(role_description) > ROLE_DESCRIPTION_MAX_LENGTH
        ):
            raise DocumentValidationError(
                "role description must be less than "
                f"{ROLE_DESCRIPTION_MAX_LENGTH} characters long!"
            )

        GPTRoleSetting.set(owner_id, role_description)

    def reset_role(self, owner_id):
        """Delete custom role description for specific owner ID."""

        setting = GPTRoleSetting.get(owner_id)
        if setting:
            setting.delete()

    def request(
        self,
        prompt: str,
        owner_id: str = None,
        use_history: bool = False,
        history_limit: int = 2,
        handle_intents: bool = False,
    ) -> str:
        """Make request to selected GPT model."""

        if owner_id:
            role_description = self.get_role(owner_id) or ROLE_DEFAULT
            messages = [self.message("system", role_description)]
            if use_history:
                previous_messages = GPTChatHistory.fetch(
                    owner_id, after_ts=dt.now() - EXPIRATION_DELTA
                )
                messages.extend(previous_messages[-history_limit * 2 :])
        else:
            messages = [self.message("system", ROLE_DEFAULT)]

        if handle_intents:
            if context := self.intent_manager.handle_prompt(prompt):
                prompt = f"{prompt}\n\nRELATED DATA:\n{context}"

        messages.append(self.message("user", prompt))
        reply = openai.ChatCompletion.create(model=self.model, messages=messages)
        assistant_msg = reply["choices"][0]["message"]["content"]

        if owner_id:
            GPTChatHistory.store(owner_id, prompt, assistant_msg)

        return assistant_msg
