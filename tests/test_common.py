"""Common-related test cases."""

import pytest

from peon_common import utils
from peon_common.exceptions import (
    CommandMalformed,
)

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
