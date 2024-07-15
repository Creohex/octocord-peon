import json
import re
import requests
from dataclasses import dataclass, field
from datetime import datetime as dt
from pathlib import Path
from string import ascii_lowercase
from typing import Self
from yarl import URL

import Levenshtein
from bs4 import BeautifulSoup as bs

from .exceptions import CommandExecutionError


@dataclass
class Price:
    value: int

    @property
    def as_string(self):
        return self.cost_int_to_str(self.value)

    @classmethod
    def from_string(cls, s: str) -> Self:
        return cls(cls.cost_str_to_int(s))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.value == other.value

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.value < other.value

    def __add__(self, other) -> Self:
        return Price(self.value + other.value)

    def __sub__(self, other) -> Self:
        return Price(self.value - other.value)

    def __mul__(self, other) -> Self:
        return Price(self.value * other.value)

    def __truediv__(self, other) -> Self:
        return Price(self.value // other.value)

    def __mod__(self, other) -> Self:
        return Price(self.value % other.value)

    def __repr__(self) -> str:
        return f"<Price:{self.as_string}>"

    @staticmethod
    def cost_str_to_int(cost_string: str) -> int:
        m = re.search(
            r"((?P<gold>\d+)g\s*)?((?P<silver>\d+)s\s*)?((?P<copper>\d+)c\s*)?",
            cost_string.strip(),
        )
        if not any(m.groupdict().values()):
            raise ValueError(f"Invalid currency string format: {cost_string}")
        return sum(
            [
                int(m.group("gold") or 0) * 10000,
                int(m.group("silver") or 0) * 100,
                int(m.group("copper") or 0),
            ]
        )

    @staticmethod
    def cost_int_to_str(value):
        return f"{value / 10000:.2f}g"


@dataclass
class Item:
    id: int
    name: str
    price: Price = field(default_factory=lambda: Price(0))
    last_updated: float = 0.0

    @property
    def price_readable(self):
        return self.price.as_string if self.price.value else "?"

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def update(self, obj: Self) -> Self:
        self.name = obj.name
        self.price = obj.price
        self.last_updated = obj.last_updated


class AHScraper:
    LINK_ALPHABET = ascii_lowercase + " 0123456789"
    LINK_PATTERN = (
        r"\[(?P<name>[\w\s#:'!\(,\.\s\-\/\&\)]+)\]\([\w\.:\-\/]+\/\?item=(?P<id>\d+)\)"
    )

    INVALIDATE_AFTER = 86400
    """Amount of seconds, after which cached items will be considered invalid."""

    def __init__(self, url: URL, items_file: Path) -> Self:
        self.url = url
        self.items_file = items_file.absolute()
        if not self.items_file.is_file():
            raise Exception(f"No file found! ({self.items_file})")

        self.items = {}
        self.cache = {}  # id: obj

        if items_file:
            with open(self.items_file, "r") as f:
                self.items = json.load(f)

    def build_query_url(self, item: Item) -> URL:
        words = "".join(c for c in item.name.lower() if c in self.LINK_ALPHABET).split()
        return self.url / f"{'-'.join(words)}-{str(item.id)}"

    def find_item(self, text: str) -> Item:
        if not text:
            return None

        text = text.lower()
        closest_item = None
        min_distance = float("inf")
        partial = [name for name in self.items if text in name]

        for item in partial:
            distance = Levenshtein.distance(text, item.lower())

            if distance < min_distance:
                min_distance = distance
                closest_item = item

        if not closest_item:
            return None

        return Item(self.items[closest_item], closest_item)

    def _query_auction(self, item: Item) -> None:
        cached = self.cache.get(item.id)
        if cached:
            if (dt.now().timestamp() - cached.last_updated) < self.INVALIDATE_AFTER:
                item.update(cached)
                return

        response = requests.get(self.build_query_url(item))
        if not response.ok:
            raise CommandExecutionError("Unable to fetch AH data from url")

        soup = bs(response.text, "html.parser")
        blocks = soup.find_all(
            lambda tag: tag.name == "td" and "Average Buyout" in tag.get_text()
        )
        if len(blocks) != 1:
            return None
        cost_block = blocks[0].find_next_sibling()
        item.price = Price.from_string(cost_block.text)
        item.last_updated = dt.now().timestamp()
        self.cache[item.id] = item

    def fetch_prices(self, text: str) -> list:
        """Try to differentiate specified items and query its prices."""

        items = set()
        t = text

        for m in re.finditer(self.LINK_PATTERN, text):
            found = self.find_item(m.group("name"))
            if found:
                items.add(found)
            t = t.replace(m.group(), "")

        if t:
            for name in t.split(","):
                found = self.find_item(name)
                if found:
                    items.add(found)

        list(map(self._query_auction, items))

        return items

    @staticmethod
    def format_item_prices(items: list[Item]) -> str:
        if not items:
            return "nothing found"
        elif len(items) == 1:
            item = items.pop()
            return f"Average price for '{item.name}': {item.price.as_string}"
        else:
            return "Avg prices: " + "; ".join(
                f"{item.name}: {item.price.as_string}" for item in items
            )
