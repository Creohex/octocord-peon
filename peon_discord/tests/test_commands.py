"""Common-related test cases."""

import pytest

import peon_discord.commands as commands


MENTION_STUB = "<@123>"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", ""),
        ("blabla?", "blabla?"),
        ("[[bob](https://some_url.com)]: blabla?", "bob says: blabla?"),
        (
            f"[[bob](https://some_url.com)]: blabla {MENTION_STUB}?",
            "bob says: blabla you?",
        ),
    ],
)
def test_sanitize_gpt_request(text, expected):
    assert commands.sanitize_gpt_request(text, MENTION_STUB) == expected
