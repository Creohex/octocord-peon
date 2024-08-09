import mock
import os
import peon_common.gpt
import pytest
import requests
from datetime import datetime
from mock import MagicMock
from pathlib import Path
from yarl import URL

from peon_common import gpt
from peon_common.db import GPTChatHistory

import openai


@pytest.fixture
def openai_mock():
    with mock.patch("openai.ChatCompletion") as openai_mock:
        openai_mock.create.return_value = {
            "choices": [{"message": {"content": "openai_reply"}}]
        }
        yield openai_mock


@pytest.fixture
def chat_history_mock():
    with mock.patch("peon_common.gpt.GPTChatHistory") as chat_history:
        yield chat_history


@pytest.fixture
def completion_mock():
    with (mock.patch("peon_common.gpt.dt") as dt,):
        dt.now.return_value = 100
        yield gpt.Completion()


def test_completion(chat_history_mock, openai_mock, completion_mock):
    reply = completion_mock.request("test")

    assert reply == "openai_reply"
    assert openai.ChatCompletion.create.call_count == 1
    create_kwargs = openai.ChatCompletion.create.call_args.kwargs
    assert create_kwargs["model"] == gpt.MODEL_DEFAULT
    assert create_kwargs["messages"][0]["role"] == gpt.MESSAGE_ROLE_SYSTEM
    assert create_kwargs["messages"][0]["content"] == gpt.ROLE_DEFAULT
    assert create_kwargs["messages"][1]["role"] == gpt.MESSAGE_ROLE_USER
    assert create_kwargs["messages"][1]["content"] == "test"
    assert chat_history_mock.store.call_count == 0


def test_completion_owner(chat_history_mock, openai_mock, completion_mock):
    test_owner = "owner1"
    test_prompt = "test_prompt"
    test_role = "test_role"
    with mock.patch.object(
        completion_mock, "get_role", return_value=test_role
    ) as get_role_mock:
        reply = completion_mock.request(test_prompt, owner_id=test_owner)

    assert reply == "openai_reply"
    create_kwargs = openai.ChatCompletion.create.call_args.kwargs
    assert create_kwargs["model"] == gpt.MODEL_DEFAULT
    assert create_kwargs["messages"][0]["role"] == gpt.MESSAGE_ROLE_SYSTEM
    assert create_kwargs["messages"][0]["content"] == test_role
    assert create_kwargs["messages"][1]["role"] == gpt.MESSAGE_ROLE_USER
    assert create_kwargs["messages"][1]["content"] == test_prompt

    get_role_mock.assert_called_once_with(test_owner)
    chat_history_mock.store.assert_called_once_with(test_owner, test_prompt, reply)

    # TODO: existing owner id + with custom role + with message history
    # TODO: intents handling


SAMPLE_INTENT_DATA = {
    "text": "current weather in Moscow?",
    "intent": {"name": "query_weather", "confidence": 0.9979630708694458},
    "entities": [],
    "text_tokens": [[0, 7], [8, 15], [16, 18], [19, 25], [25, 26]],
    "intent_ranking": [
        {"name": "query_weather", "confidence": 0.9979630708694458},
        {"name": "goodbye", "confidence": 9.82042183750309e-5},
        {"name": "mood_great", "confidence": 3.840781209873967e-5},
        {"name": "affirm", "confidence": 3.5008844861295074e-5},
        {"name": "intent_fallback", "confidence": 3.013433342857752e-5},
    ],
}


@pytest.fixture
def rasa_env():
    os.environ[gpt.RASA_PROVIDER_URL_ENV] = "http://localhost:5005"

# TODO: intent provider
def test_rasa_provider(rasa_env):
    intent_provider = gpt.RasaLocal()
    x = intent_provider.get_intent("what's the current weather?")
    import pdb; pdb.set_trace()


# TODO: intent manager
# TODO: completion
# TODO: completion mocks for all classes above that use Completion.request()/etc
