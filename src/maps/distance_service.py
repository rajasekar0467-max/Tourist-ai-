import requests


def get_route_distance(start: str, destination: str):
    """
    Get approximate driving distance using a free
    OpenStreetMap-based routing service.
    """

    headers = {
        "User-Agent": "TouristAI/1.0"
    }

    # Geocode starting location
    start_response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": start,
            "format": "json",
            "limit": 1
        },
        headers=headers,
        timeout=10
    )

    start_data = start_response.json()

    if not start_data:
        raise ValueError(f"Could not find location: {start}")

    start_lat = float(start_data[0]["lat"])
    start_lon = float(start_data[0]["lon"])

    # Geocode destination
    destination_response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": destination,
            "format": "json",
            "limit": 1
        },
        headers=headers,
        timeout=10
    )

    destination_data = destination_response.json()

    if not destination_data:
        raise ValueError(
            f"Could not find location: {destination}"
        )

    destination_lat = float(destination_data[0]["lat"])
    destination_lon = float(destination_data[0]["lon"])

    # OSRM routing
    route_url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};"
        f"{destination_lon},{destination_lat}"
    )

    route_response = requests.get(
        route_url,
        params={
            "overview": "false"
        },
        timeout=15
    )

    route_data = route_response.json()

    if route_data.get("code") != "Ok":
        raise ValueError("Could not calculate the route.")

    route = route_data["routes"][0]

    distance_km = route["distance"] / 1000
    duration_minutes = route["duration"] / 60

    return {
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 0),
        "start": start,
        "destination": destination
    }
