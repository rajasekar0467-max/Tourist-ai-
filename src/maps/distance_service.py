import requests
from urllib.parse import quote


NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

OSRM_URL = (
    "https://router.project-osrm.org/route/v1/driving/"
)


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent": (
            "TouristAI/1.0 "
            "(Educational Travel Planning Application)"
        ),
        "Accept": "application/json"
    }
)


# ============================================================
# GEOCODE LOCATION
# ============================================================

def geocode_location(location: str):
    """
    Convert a location name into coordinates
    using OpenStreetMap Nominatim.
    """

    if not isinstance(location, str):

        raise ValueError(
            "Location must be text."
        )

    location = location.strip()

    if not location:

        raise ValueError(
            "Location cannot be empty."
        )

    try:

        response = session.get(
            NOMINATIM_URL,
            params={
                "q": location,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as error:

        raise ConnectionError(
            f"Location search failed: {error}"
        ) from error

    if not data:

        raise ValueError(
            f"Location not found: {location}"
        )

    best_match = data[0]

    try:

        latitude = float(
            best_match["lat"]
        )

        longitude = float(
            best_match["lon"]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ) as error:

        raise ValueError(
            f"Invalid location data for: {location}"
        ) from error

    return {
        "latitude": latitude,
        "longitude": longitude,
        "display_name": best_match.get(
            "display_name",
            location
        )
    }


# ============================================================
# GOOGLE MAPS URL
# ============================================================

def create_google_maps_url(
    start: str,
    destination: str
):
    """
    Create a Google Maps directions URL.

    Uses query parameters instead of manually
    building a complex Maps URL.
    """

    start_encoded = quote(
        start.strip(),
        safe=""
    )

    destination_encoded = quote(
        destination.strip(),
        safe=""
    )

    return (
        "https://www.google.com/maps/dir/"
        f"{start_encoded}/"
        f"{destination_encoded}/"
        "?travelmode=driving"
    )


# ============================================================
# GET ROUTE DISTANCE
# ============================================================

def get_route_distance(
    start: str,
    destination: str
):
    """
    Calculate driving route.

    Uses:
    - OpenStreetMap Nominatim
    - OSRM routing
    - Google Maps navigation URL
    """

    start = str(start).strip()
    destination = str(destination).strip()

    if not start:

        raise ValueError(
            "Starting location cannot be empty."
        )

    if not destination:

        raise ValueError(
            "Destination cannot be empty."
        )

    # --------------------------------------------------------
    # GEOCODE
    # --------------------------------------------------------

    start_location = geocode_location(
        start
    )

    destination_location = geocode_location(
        destination
    )

    # --------------------------------------------------------
    # OSRM COORDINATES
    # Format: longitude,latitude;longitude,latitude
    # --------------------------------------------------------

    coordinates = (
        f"{start_location['longitude']},"
        f"{start_location['latitude']};"
        f"{destination_location['longitude']},"
        f"{destination_location['latitude']}"
    )

    route_url = (
        OSRM_URL + coordinates
    )

    # --------------------------------------------------------
    # GET ROUTE
    # --------------------------------------------------------

    try:

        response = session.get(
            route_url,
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "false"
            },
            timeout=30
        )

        response.raise_for_status()

        route_data = response.json()

    except requests.RequestException as error:

        raise ConnectionError(
            f"Route service failed: {error}"
        ) from error

    if route_data.get("code") != "Ok":

        message = route_data.get(
            "message",
            "Could not calculate driving route."
        )

        raise ValueError(message)

    routes = route_data.get(
        "routes",
        []
    )

    if not routes:

        raise ValueError(
            "No driving route found."
        )

    route = routes[0]

    # --------------------------------------------------------
    # ROUTE GEOMETRY
    # OSRM: [longitude, latitude]
    # FOLIUM: [latitude, longitude]
    # --------------------------------------------------------

    geometry = route.get(
        "geometry",
        {}
    )

    coordinates_data = geometry.get(
        "coordinates",
        []
    )

    route_points = []

    for point in coordinates_data:

        if (
            isinstance(point, list)
            and len(point) >= 2
        ):

            longitude = point[0]
            latitude = point[1]

            route_points.append(
                [
                    latitude,
                    longitude
                ]
            )

    # --------------------------------------------------------
    # DISTANCE + TIME
    # --------------------------------------------------------

    distance_meters = float(
        route.get(
            "distance",
            0
        )
    )

    duration_seconds = float(
        route.get(
            "duration",
            0
        )
    )

    distance_km = round(
        distance_meters / 1000,
        2
    )

    duration_minutes = round(
        duration_seconds / 60
    )

    if distance_km <= 0:

        raise ValueError(
            "Invalid route distance received."
        )

    # --------------------------------------------------------
    # GOOGLE MAPS
    # --------------------------------------------------------

    google_maps_url = create_google_maps_url(
        start_location["display_name"],
        destination_location["display_name"]
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

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
