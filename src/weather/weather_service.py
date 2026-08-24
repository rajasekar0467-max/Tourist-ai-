import requests


WEATHER_CODES = {
    0: "☀️ Clear sky",
    1: "🌤️ Mainly clear",
    2: "⛅ Partly cloudy",
    3: "☁️ Overcast",
    45: "🌫️ Foggy",
    48: "🌫️ Rime fog",
    51: "🌦️ Light drizzle",
    53: "🌦️ Moderate drizzle",
    55: "🌧️ Heavy drizzle",
    56: "🌧️ Freezing drizzle",
    57: "🌧️ Heavy freezing drizzle",
    61: "🌦️ Slight rain",
    63: "🌧️ Moderate rain",
    65: "🌧️ Heavy rain",
    66: "🌧️ Freezing rain",
    67: "🌧️ Heavy freezing rain",
    71: "🌨️ Slight snowfall",
    73: "🌨️ Moderate snowfall",
    75: "❄️ Heavy snowfall",
    77: "🌨️ Snow grains",
    80: "🌦️ Slight rain showers",
    81: "🌧️ Moderate rain showers",
    82: "⛈️ Violent rain showers",
    85: "🌨️ Slight snow showers",
    86: "❄️ Heavy snow showers",
    95: "⛈️ Thunderstorm",
    96: "⛈️ Thunderstorm with slight hail",
    99: "⛈️ Thunderstorm with heavy hail",
}


def get_weather(latitude, longitude):
    """
    Get current weather from Open-Meteo.

    Returns current destination weather
    using the destination's local timezone.
    """

    if latitude is None or longitude is None:
        raise ValueError(
            "Destination coordinates are required."
        )

    latitude = float(latitude)
    longitude = float(longitude)

    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude.")

    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude.")

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "weather_code,"
            "wind_speed_10m,"
            "is_day"
        ),

        "timezone": "auto"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    current = data.get("current")

    if not current:
        raise ValueError(
            "Current weather data is unavailable."
        )

    return {
        "temperature": round(
            float(current.get("temperature_2m", 0)),
            1
        ),

        "feels_like": round(
            float(current.get("apparent_temperature", 0)),
            1
        ),

        "humidity": int(
            current.get(
                "relative_humidity_2m",
                0
            )
        ),

        "wind_speed": round(
            float(
                current.get(
                    "wind_speed_10m",
                    0
                )
            ),
            1
        ),

        "weather_code": int(
            current.get(
                "weather_code",
                -1
            )
        ),

        "is_day": bool(
            current.get(
                "is_day",
                1
            )
        ),

        "time": current.get(
            "time",
            ""
        ),

        "timezone": data.get(
            "timezone",
            "auto"
        )
    }


def weather_description(code):
    """
    Convert WMO weather code into
    a human-readable description.
    """

    return WEATHER_CODES.get(
        int(code),
        "🌍 Weather condition unavailable"
    )


def get_weather_advice(weather):
    """
    Create simple travel advice
    based on current weather.
    """

    if not weather:
        return "Weather data is not available."

    code = weather.get(
        "weather_code",
        -1
    )

    temperature = weather.get(
        "temperature",
        0
    )

    if code in [61, 63, 65, 80, 81, 82]:
        return (
            "☔ Rain possible. Carry an umbrella "
            "or raincoat."
        )

    if code in [95, 96, 99]:
        return (
            "⚠️ Thunderstorm conditions. "
            "Avoid exposed outdoor areas."
        )

    if temperature >= 35:
        return (
            "☀️ Hot weather. Carry water and "
            "avoid long outdoor activity at noon."
        )

    if temperature <= 15:
        return (
            "🧥 Cool weather. Carry suitable "
            "warm clothing."
        )

    return (
        "✅ Weather looks generally suitable "
        "for travel."
    )
