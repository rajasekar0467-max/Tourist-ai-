import requests
from urllib.parse import quote


NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

OSRM_URL = (
    "https://router.project-osrm.org/"
    "route/v1/driving/"
)


def geocode_location(location: str):
    """
    Convert a location name into coordinates
    using OpenStreetMap Nominatim.
    """

    location = location.strip()

    if not location:
        raise ValueError(
            "Location cannot be empty."
        )

    headers = {
        "User-Agent": (
            "TouristAI/1.0 "
            "(Travel Planning Application)"
        )
    }

    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": location,
            "format": "jsonv2",
            "limit": 5,
            "addressdetails": 1
        },
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise ValueError(
            f"Location not found: {location}"
        )

    # Use the best matching result
    best_match = data[0]

    return {
        "latitude": float(
            best_match["lat"]
        ),

        "longitude": float(
            best_match["lon"]
        ),

        "display_name": best_match.get(
            "display_name",
            location
        )
    }


def create_google_maps_url(
    start: str,
    destination: str
):
    """
    Create a Google Maps driving navigation URL.
    """

    start_encoded = quote(start)
    destination_encoded = quote(destination)

    return (
        "https://www.google.com/maps/dir/"
        f"{start_encoded}/"
        f"{destination_encoded}/"
        "data=!4m2!4m1!3e0"
    )


def get_route_distance(
    start: str,
    destination: str
):
    """
    Calculate driving route.

    Uses:
    - OpenStreetMap Nominatim for coordinates
    - OSRM for route calculation
    - Google Maps URL for navigation
    """

    # ------------------------------------------------
    # GEOCODE LOCATIONS
    # ------------------------------------------------

    start_location = geocode_location(
        start
    )

    destination_location = geocode_location(
        destination
    )

    # ------------------------------------------------
    # CREATE OSRM ROUTE URL
    # ------------------------------------------------

    coordinates = (
        f"{start_location['longitude']},"
        f"{start_location['latitude']};"
        f"{destination_location['longitude']},"
        f"{destination_location['latitude']}"
    )

    route_url = (
        OSRM_URL +
        coordinates
    )

    # ------------------------------------------------
    # GET ROUTE
    # ------------------------------------------------

    response = requests.get(
        route_url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        },
        timeout=30
    )

    response.raise_for_status()

    route_data = response.json()

    if route_data.get("code") != "Ok":

        raise ValueError(
            "Could not calculate the driving route."
        )

    routes = route_data.get(
        "routes",
        []
    )

    if not routes:

        raise ValueError(
            "No driving route found."
        )

    route = routes[0]

    # ------------------------------------------------
    # ROUTE GEOMETRY
    # OSRM = longitude, latitude
    # Folium = latitude, longitude
    # ------------------------------------------------

    geometry = (
        route
        .get("geometry", {})
        .get("coordinates", [])
    )

    route_points = [
        [
            point[1],
            point[0]
        ]
        for point in geometry
    ]

    # ------------------------------------------------
    # DISTANCE + TIME
    # ------------------------------------------------

    distance_km = round(
        route["distance"] / 1000,
        2
    )

    duration_minutes = round(
        route["duration"] / 60
    )

    # ------------------------------------------------
    # GOOGLE MAPS NAVIGATION
    # ------------------------------------------------

    google_maps_url = (
        create_google_maps_url(
            start,
            destination
        )
    )

    # ------------------------------------------------
    # RETURN COMPLETE ROUTE
    # ------------------------------------------------

    return {
        "start": start,
        "destination": destination,

        "start_display_name":
            start_location["display_name"],

        "destination_display_name":
            destination_location["display_name"],

        "distance_km":
            distance_km,

        "duration_minutes":
            duration_minutes,

        "start_latitude":
            start_location["latitude"],

        "start_longitude":
            start_location["longitude"],

        "destination_latitude":
            destination_location["latitude"],

        "destination_longitude":
            destination_location["longitude"],

        "route_points":
            route_points,

        "google_maps_url":
            google_maps_url
    }
