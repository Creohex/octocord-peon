import mock
import os
import pytest

from peon_common import misc


SAMPLE_WEATHER_REPLY = {
    "coord": {"lon": -0.1257, "lat": 51.5085},
    "weather": [
        {"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}
    ],
    "base": "stations",
    "main": {
        "temp": 292.84,
        "feels_like": 292.88,
        "temp_min": 291.4,
        "temp_max": 294.06,
        "pressure": 1013,
        "humidity": 77,
        "sea_level": 1013,
        "grnd_level": 1009,
    },
    "visibility": 10000,
    "wind": {"speed": 7.72, "deg": 270},
    "clouds": {"all": 75},
    "dt": 1723190888,
    "sys": {
        "type": 2,
        "id": 2075535,
        "country": "GB",
        "sunrise": 1723178226,
        "sunset": 1723232096,
    },
    "timezone": 3600,
    "id": 2643743,
    "name": "test_location",
    "cod": 200,
}


@pytest.fixture(autouse=True)
def prep():
    os.environ[misc.OPENWEATHER_TOKEN] = "test_key"
    response_mock = mock.MagicMock(json=lambda: SAMPLE_WEATHER_REPLY)

    with mock.patch("requests.get", return_value=response_mock):
        yield


def test_weather():
    assert misc.Weather().query_weather("test_location") == {
        "location": "test_location",
        "description": "Clouds",
        "description_extra": "broken clouds",
        "temperature": "19.7, feels like 19.7 (celsius)",
        "humidity": "77%",
        "pressure": "1013hPa",
        "wind": "7.72m/s, W",
        "clouds": "75%",
    }
