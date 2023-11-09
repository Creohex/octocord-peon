import os

import openai

from peon_common.db import GPTRoleSetting
from peon_common.exceptions import LogicalError, DocumentValidationError
from peon_common.models import Singleton


MAX_TOKENS = 1000
"""Maximum tokens per completion."""

MODEL_DEFAULT = "gpt-3.5-turbo"
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


# TODO: show billing/usage
class Completion(Singleton):
    """GPT interation model."""

    def __init__(self) -> None:
        openai.api_key = os.environ["openai_token"]
        self.model = MODEL_DEFAULT
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE_DEFAULT

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

    # TODO: support supplying GPT with previous messages for context
    def request(self, prompt: str, owner_id: str = None) -> str:
        """Make request to selected GPT model."""

        if owner_id:
            role_description = self.get_role(owner_id) or ROLE_DEFAULT
        else:
            role_description = ROLE_DEFAULT

        return openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": role_description or ROLE_DEFAULT,
                },
                {"role": "user", "content": prompt},
            ],
        )["choices"][0]["message"]["content"]
