import requests


def geocode_location(location: str):
    """
    Convert a place name into latitude and longitude
    using OpenStreetMap Nominatim.
    """

    headers = {
        "User-Agent": "TouristAI/1.0"
    }

    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": location,
            "format": "json",
            "limit": 1
        },
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise ValueError(
            f"Could not find location: {location}"
        )

    return {
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"]),
        "display_name": data[0]["display_name"]
    }


def get_route_distance(start: str, destination: str):

    start_location = geocode_location(start)
    destination_location = geocode_location(
        destination
    )

    route_url = (
        "https://router.project-osrm.org/"
        "route/v1/driving/"
        f"{start_location['longitude']},"
        f"{start_location['latitude']};"
        f"{destination_location['longitude']},"
        f"{destination_location['latitude']}"
    )

    response = requests.get(
        route_url,
        params={
            "overview": "false"
        },
        timeout=15
    )

    response.raise_for_status()

    route_data = response.json()

    if route_data.get("code") != "Ok":
        raise ValueError(
            "Could not calculate the route."
        )

    route = route_data["routes"][0]

    return {
        "start": start,
        "destination": destination,
        "distance_km": round(
            route["distance"] / 1000,
            2
        ),
        "duration_minutes": round(
            route["duration"] / 60,
            0
        ),
        "start_latitude": start_location["latitude"],
        "start_longitude": start_location["longitude"],
        "destination_latitude":
            destination_location["latitude"],
        "destination_longitude":
            destination_location["longitude"]
    }

    
