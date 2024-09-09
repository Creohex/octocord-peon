import mock
import pytest
import requests
from pathlib import Path
from yarl import URL

from peon_common.ah import AHScraper, Item, Price


AH_BASE_URL = "https://www.wowauctions.net/auctionHouse"
NORDNAAR_AH_SCRAPER = AHScraper(
    f"{AH_BASE_URL}/turtle-wow/nordanaar/mergedAh/", Path("peon_common/twow_items.json")
)


TEST_DIR = Path(__file__).resolve(strict=True).parent
GAME_ITEMS_FILE = TEST_DIR.parent / "twow_items.json"
AH_REPLY_EXAMPLE_FILE = TEST_DIR / "ah_reply_example.html"
TEST_URL = URL("https://bla.qwe/")

with open(AH_REPLY_EXAMPLE_FILE, "r") as f:
    AH_REPLY_EXAMPLE = f.read().replace("\n", "")


@pytest.fixture()
def scraper():
    ah_scraper = AHScraper(TEST_URL, TEST_DIR.parent / "twow_items.json")
    response_mock = mock.MagicMock(text=AH_REPLY_EXAMPLE)

    with mock.patch.object(requests, "get", return_value=response_mock):
        yield ah_scraper


def test_price():
    p1 = Price(0)
    assert p1.value == 0
    assert p1.as_string == "0.00g"
    assert p1 == Price(0)

    p2 = Price(152535)
    assert p2.value == 152535
    assert p2.as_string == "15.25g"
    assert p2 > p1
    assert p2 - Price(2535) == Price(150000)

    p3 = Price.from_string("1g 22s33c")
    assert p3.value == 12233
    assert p3.as_string == "1.22g"
    assert p3.value == Price(12233).value

    with pytest.raises(ValueError):
        Price.from_string("gibberish")


@pytest.mark.parametrize(
    ("item", "expected_url"),
    [
        (Item(0, "item0"), TEST_URL / "item0-0"),
        (
            Item(123, "A rather complex 'string' #abc!"),
            TEST_URL / "a-rather-complex-string-abc-123",
        ),
    ],
)
def test_build_query_url(scraper, item, expected_url):
    complete_url = scraper.build_query_url(item)
    assert complete_url == expected_url
    assert isinstance(complete_url, URL)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", None),
        ("gibberish", None),
        ("dream", "dreamfoil"),
        ("greater int", "elixir of greater intellect"),
        ("bl", "bleach"),
        ("copper bar", "copper bar"),
        ("major mana", "major mana potion"),
        ("1", "the 1 ring"),
        ("&", "red & blue mechanostrider"),
        ("n-", "ginn-su sword"),
        ("Headstriker Sword of the Bear", "headstriker sword"),
        ("Bloodforged Chestpiece of the Monkey", "bloodforged chestpiece"),
        ("Coral Band of Regeneration", "coral band"),
        ("Green Lens of Nature's Wrath", "green lens"),
    ],
)
def test_find_item(scraper, query, expected):
    found = scraper.find_item(query)

    if expected:
        assert found.name == expected
    else:
        assert found is None


def test_query_auction(scraper):
    item = Item(61224, "Dreamshared Elixir")
    assert item.price.value == 0

    scraper._query_auction(item)
    assert item.price.value == 15900


def test_query_auction_caching(scraper):
    item = Item(61224, "Dreamshared Elixir")
    assert item.price.value == 0

    with mock.patch.object(
        requests, "get", return_value=mock.MagicMock(text=AH_REPLY_EXAMPLE)
    ) as get_mock:
        scraper._query_auction(item)
        assert item.price.value == 15900
        assert get_mock.call_count == 1

        with mock.patch("peon_common.ah.dt") as dt:
            ts = mock.MagicMock()
            dt.now.return_value.timestamp = ts

            item.last_updated = 500
            ts.return_value=501
            scraper._query_auction(item)
            assert get_mock.call_count == 1

            ts.return_value = item.last_updated + scraper.INVALIDATE_AFTER - 1
            scraper._query_auction(item)
            assert get_mock.call_count == 1

            ts.return_value = item.last_updated + scraper.INVALIDATE_AFTER
            scraper._query_auction(item)
            assert get_mock.call_count == 2


@pytest.mark.parametrize(
    ("text", "found_items"),
    [
        ("", 0),
        ("gibberish", 0),
        ("dreamsha", 1),
        ("Tellurium Band of Concentration", 1),
        ("[broom](https://database.turtle-wow.org/?item=0)", 1),
        ("[broom](https://database.turtle-wow.org/?item=0) major rejuv", 2),
        (
            "[broom](https://database.turtle-wow.org/?item=0) "
            "gibberish, major mana pot,"
            "[snow](https://database.turtle-wow.org/?item=0), limited invul",
            4,
        ),
    ],
)
def test_fetch_prices(scraper, text, found_items):
    with mock.patch.object(AHScraper, "_query_auction", return_value=123):
        items = scraper.fetch_prices(text)
        assert len(items) == found_items
