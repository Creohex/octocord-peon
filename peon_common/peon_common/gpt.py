import os
from datetime import datetime, timedelta

import openai

from peon_common.db import GPTChatHistory, GPTRoleSetting
from peon_common.exceptions import DocumentValidationError, ValidationError
from peon_common.models import Singleton


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
because this chat will happen in messaging apps such as telegram.
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

ROLE_DESCRIPTION_MAX_LENGTH = 600
"""Maximum string length for custom role descriptions."""

MESSAGE_ROLE_TYPES = ["system", "user", "assistant", "tool"]
"""Existing completion role types."""

EXPIRATION_DELTA = timedelta(days=1)
"""Default delta to consider GPT interaction as expired."""


# TODO: fetch/show billing/usage
class Completion(Singleton):
    """GPT interation model."""

    def __init__(self) -> None:
        openai.api_key = os.environ["openai_token"]
        self.model = MODEL_DEFAULT
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE_DEFAULT

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
        use_history=False,
        history_limit=2,
    ) -> str:
        """Make request to selected GPT model."""

        if not owner_id:
            return openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    self.message("system", ROLE_DEFAULT),
                    self.message("user", prompt),
                ],
            )["choices"][0]["message"]["content"]

        role_description = self.get_role(owner_id) or ROLE_DEFAULT
        messages = [self.message("system", role_description)]
        if use_history:
            previous_messages = GPTChatHistory.fetch(
                owner_id, after_ts=datetime.now() - EXPIRATION_DELTA
            )
            messages.extend(previous_messages[-history_limit * 2 :])
        messages.append(self.message("user", prompt))

        reply = openai.ChatCompletion.create(model=self.model, messages=messages)
        assistant_msg = reply["choices"][0]["message"]["content"]
        GPTChatHistory.store(owner_id, prompt, assistant_msg)

        return assistant_msg
