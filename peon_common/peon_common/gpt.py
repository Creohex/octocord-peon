import os

import openai

from peon_common.models import Singleton


MAX_TOKENS = 1000
"""Maximum tokens per completion."""

MODEL_DEFAULT = "gpt-3.5-turbo"
"""Default model used for completions."""

TEMPERATURE_DEFAULT = 0.3
"""Default temperature."""

ROLE_PEON = """\
You are a helpful orcish peon (warcraft universe).
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
ROLES = {
    "peon": ROLE_PEON,
    "assistant": ROLE_ASSISTANT,
}
"""GPT chat role descriptions."""


# TODO: show billing/usage
class Completion(Singleton):
    """GPT interation model."""

    def __init__(self) -> None:
        openai.api_key = os.environ["openai_token"]
        self.model = MODEL_DEFAULT
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE_DEFAULT

    def list_models(self):
        return openai.Model.list()

    # TODO: support supplying GPT with previous messages
    def request(self, prompt, role=None):
        return openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ROLES.get(role, ROLE_PEON)},
                {"role": "user", "content": prompt},
            ],
        )["choices"][0]["message"]["content"]
