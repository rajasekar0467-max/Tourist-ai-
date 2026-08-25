import requests


WEATHER_DESCRIPTIONS = {
    0: "☀️ Clear sky",
    1: "🌤️ Mainly clear",
    2: "⛅ Partly cloudy",
    3: "☁️ Overcast",
    45: "🌫️ Foggy",
    48: "🌫️ Depositing rime fog",
    51: "🌦️ Light drizzle",
    53: "🌦️ Moderate drizzle",
    55: "🌧️ Dense drizzle",
    56: "🌧️ Light freezing drizzle",
    57: "🌧️ Heavy freezing drizzle",
    61: "🌦️ Slight rain",
    63: "🌧️ Moderate rain",
    65: "🌧️ Heavy rain",
    66: "🌧️ Light freezing rain",
    67: "🌧️ Heavy freezing rain",
    71: "🌨️ Slight snowfall",
    73: "🌨️ Moderate snowfall",
    75: "❄️ Heavy snowfall",
    77: "❄️ Snow grains",
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

    if latitude is None or longitude is None:
        raise ValueError(
            "Destination coordinates are required."
        )

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
        "timezone": "auto",
        "forecast_days": 1
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    if "current" not in data:
        raise ValueError(
            "Current weather data is not available."
        )

    current = data["current"]

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
            current.get("relative_humidity_2m", 0)
        ),
        "wind_speed": round(
            float(current.get("wind_speed_10m", 0)),
            1
        ),
        "weather_code": int(
            current.get("weather_code", -1)
        ),
        "is_day": bool(
            current.get("is_day", True)
        ),
        "time": current.get(
            "time",
            "Unknown"
        ),
        "timezone": data.get(
            "timezone",
            "Local"
        )
    }


def weather_description(code):

    try:
        code = int(code)
    except (TypeError, ValueError):
        return "🌍 Weather information unavailable"

    return WEATHER_DESCRIPTIONS.get(
        code,
        "🌍 Weather information unavailable"
    )


def get_weather_advice(weather):

    if not weather:
        return (
            "Weather information is not available."
        )

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
            "🌧️ Rain possibility: Carry an umbrella "
            "or raincoat. Check outdoor plans."
        )

    if code in [95, 96, 99]:
        return (
            "⛈️ Thunderstorm conditions: Avoid exposed "
            "outdoor areas and check local alerts."
        )

    if temperature >= 35:
        return (
            "🥵 Hot weather: Carry water, use sunscreen "
            "and avoid long outdoor activity at noon."
        )

    if temperature <= 15:
        return (
            "🧥 Cool weather: Carry suitable warm clothing."
        )

    return (
        "👍 Weather looks generally suitable for travel. "
        "Still check conditions again before leaving."
    )
