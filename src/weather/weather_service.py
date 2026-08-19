import requests


def get_weather(latitude, longitude):
    """
    Get current weather using Open-Meteo.
    No API key required.
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]

    return {
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
    }


def weather_description(code):
    """
    Convert Open-Meteo weather code
    into a simple description.
    """

    descriptions = {
        0: "☀️ Clear sky",
        1: "🌤️ Mainly clear",
        2: "⛅ Partly cloudy",
        3: "☁️ Overcast",
        45: "🌫️ Foggy",
        48: "🌫️ Foggy",
        51: "🌦️ Light drizzle",
        53: "🌦️ Drizzle",
        55: "🌧️ Heavy drizzle",
        61: "🌧️ Light rain",
        63: "🌧️ Rain",
        65: "🌧️ Heavy rain",
        71: "🌨️ Light snow",
        73: "🌨️ Snow",
        75: "❄️ Heavy snow",
        80: "🌦️ Rain showers",
        81: "🌦️ Rain showers",
        82: "⛈️ Heavy rain showers",
        95: "⛈️ Thunderstorm",
        96: "⛈️ Thunderstorm with hail",
        99: "⛈️ Severe thunderstorm",
    }

    return descriptions.get(
        code,
        "🌍 Unknown weather"
    )
