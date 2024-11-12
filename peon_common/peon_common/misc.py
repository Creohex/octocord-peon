"""Miscellaneous stuff."""

import os
import requests
from yarl import URL

from peon_common.exceptions import LogicalError


OPENWEATHER_TOKEN = "openweather_token"


class Singleton:
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Weather(Singleton):
    URL_COORDS = URL("http://api.openweathermap.org/geo/1.0/direct")
    URL_WEATHER = URL("http://api.openweathermap.org/data/2.5/weather")

    def __init__(self) -> None:
        self.api_key = os.environ[OPENWEATHER_TOKEN]

    # TODO: caching
    def query_weather(self, location: str) -> dict:
        if not location:
            raise LogicalError()

        try:
            response = requests.get(
                self.URL_WEATHER.with_query(
                    {"q": location.strip(), "appid": self.api_key}
                ),
                timeout=5,
            )
        except requests.ConnectionError:
            return "service is not currently available"
        data = response.json()

        if not response.ok:
            if "message" in data:
                return {
                    "location": location,
                    "error_message": data["message"],
                }
            return {"error_message": "something went wrong"}

        formatted = {
            "location": data["name"],
            "description": data["weather"][0]["main"],
            "description_extra": data["weather"][0]["description"],
            "temperature": f"{data['main']['temp'] - 273.15:.1f}, feels like {data['main']['feels_like'] - 273.15:.1f} (celsius)",
            "humidity": f"{data['main']['humidity']}%",
            "pressure": f"{data['main']['pressure']}hPa",
        }
        if "wind" in data:
            formatted["wind"] = (
                f"{data['wind']['speed']}m/s, "
                f"{self.format_direction(data['wind']['deg'])}"
            )
        if "clouds" in data:
            formatted["clouds"] = f"{data['clouds']['all']}%"
        if "rain" in data:
            formatted["rain"] = f"{data['rain']} (last x hours, mm)"
        if "snow" in data:
            formatted["snow"] = f"{data['snow']} (last x hours, mm)"

        return formatted

    @staticmethod
    def format_direction(degrees: int) -> str:
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        return directions[(int((degrees / 22.5) + 0.5) % 16)]
