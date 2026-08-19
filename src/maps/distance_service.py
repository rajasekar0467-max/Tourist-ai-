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
    """
    Calculate driving route between two locations.

    Uses:
    - OpenStreetMap Nominatim for geocoding
    - OSRM for driving route calculation
    """

    # --------------------------------------------------------
    # START LOCATION
    # --------------------------------------------------------

    start_location = geocode_location(start)

    # --------------------------------------------------------
    # DESTINATION
    # --------------------------------------------------------

    destination_location = geocode_location(
        destination
    )

    # --------------------------------------------------------
    # OSRM ROUTE
    # --------------------------------------------------------

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
            "overview": "full",
            "geometries": "geojson"
        },
        timeout=20
    )

    response.raise_for_status()

    route_data = response.json()

    if route_data.get("code") != "Ok":
        raise ValueError(
            "Could not calculate the driving route."
        )

    route = route_data["routes"][0]

    # --------------------------------------------------------
    # ROUTE GEOMETRY
    # --------------------------------------------------------

    geometry = route["geometry"]["coordinates"]

    # OSRM:
    # [longitude, latitude]
    #
    # Folium:
    # [latitude, longitude]

    route_points = [
        [point[1], point[0]]
        for point in geometry
    ]

    # --------------------------------------------------------
    # FINAL ROUTE DATA
    # --------------------------------------------------------

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

        "start_latitude":
            start_location["latitude"],

        "start_longitude":
            start_location["longitude"],

        "destination_latitude":
            destination_location["latitude"],

        "destination_longitude":
            destination_location["longitude"],

        "route_points": route_points
    }
