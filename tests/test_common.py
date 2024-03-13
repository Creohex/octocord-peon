"""Common-related test cases."""

import pytest

from peon_common import utils
from peon_common.exceptions import (
    CommandMalformed,
)

from peon_telegram.handlers import sanitize_markdown

# TODO: complete cases..


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", ""),
        ("<,$%[ ]", ""),
        ("--. .. -... -... . .-. .. ... ....", "gibberish"),
        (".---- ..--- ...-- .-.-.- ..--.. -.--. -.--.-   -..-.", "123.?() /"),
    ],
)
def test_from_morse(text, expected):
    assert utils.from_morse(text) == expected


@pytest.mark.parametrize(
    ("invalid_text", "err"),
    [
        (None, CommandMalformed),
        (123, CommandMalformed),
    ],
)
def test_from_morse_negative(invalid_text, err):
    with pytest.raises(err):
        utils.from_morse(invalid_text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (r"bla", r"bla"),
        (r"bla_bla", r"bla\_bla"),
        (r"`bla_bla`", r"`bla_bla`"),
        (r"bla_bla `abc_abc`", r"bla\_bla `abc_abc`"),
        (r"```bla_bla```", r"```bla_bla```"),
        (
            r"bla_bla `bla_bla` abc_abc ```bla_bla```",
            r"bla\_bla `bla_bla` abc\_abc ```bla_bla```",
        ),
    ],
)
def test_sanitize_markdown(text, expected):
    assert sanitize_markdown(text) == expected
