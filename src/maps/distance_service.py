import time
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
        # Keep a clear application identification.
        # If you publish the app publicly, replace the contact
        # part with your own valid contact information.
        "User-Agent": (
            "TouristAI/1.0 "
            "(Educational Travel Planning Application)"
        ),
        "Accept": "application/json",
        "Accept-Language": "en"
    }
)


# ============================================================
# SIMPLE IN-MEMORY GEOCODE CACHE
# ============================================================

_GEOCODE_CACHE = {}

# Minimum delay between Nominatim requests from this process.
# This helps prevent accidental rapid requests.
_LAST_NOMINATIM_REQUEST = 0.0

NOMINATIM_MIN_DELAY = 1.1


# ============================================================
# NOMINATIM REQUEST
# ============================================================

def _nominatim_request(location: str):
    """
    Perform a controlled Nominatim request.

    Uses:
    - in-memory cache
    - minimum request interval
    - limited retry for 429 / temporary server errors
    """

    global _LAST_NOMINATIM_REQUEST

    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    cache_key = location.strip().lower()

    if cache_key in _GEOCODE_CACHE:

        return _GEOCODE_CACHE[cache_key]

    # --------------------------------------------------------
    # REQUEST ATTEMPTS
    # --------------------------------------------------------

    max_attempts = 3

    for attempt in range(max_attempts):

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        elapsed = (
            time.monotonic()
            - _LAST_NOMINATIM_REQUEST
        )

        if elapsed < NOMINATIM_MIN_DELAY:

            time.sleep(
                NOMINATIM_MIN_DELAY - elapsed
            )

        try:

            _LAST_NOMINATIM_REQUEST = (
                time.monotonic()
            )

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

            # ------------------------------------------------
            # RATE LIMITED
            # ------------------------------------------------

            if response.status_code == 429:

                if attempt < max_attempts - 1:

                    # Wait progressively longer.
                    wait_seconds = 3 * (
                        2 ** attempt
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                raise ConnectionError(
                    "Nominatim rate limit reached. "
                    "Please wait a little longer and try again."
                )

            # ------------------------------------------------
            # TEMPORARY SERVER ERRORS
            # ------------------------------------------------

            if response.status_code in (
                500,
                502,
                503,
                504
            ):

                if attempt < max_attempts - 1:

                    time.sleep(
                        2 * (attempt + 1)
                    )

                    continue

            response.raise_for_status()

            data = response.json()

            # ------------------------------------------------
            # CACHE SUCCESSFUL RESULT
            # ------------------------------------------------

            _GEOCODE_CACHE[cache_key] = data

            return data

        except requests.RequestException as error:

            if attempt < max_attempts - 1:

                time.sleep(
                    2 * (attempt + 1)
                )

                continue

            raise ConnectionError(
                f"Location search failed: {error}"
            ) from error

    raise ConnectionError(
        "Location search failed."
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

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    data = _nominatim_request(
        location
    )

    # --------------------------------------------------------
    # NO RESULT
    # --------------------------------------------------------

    if not data:

        raise ValueError(
            f"Location not found: {location}"
        )

    best_match = data[0]

    # --------------------------------------------------------
    # COORDINATES
    # --------------------------------------------------------

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
    - OpenStreetMap Nominatim for geocoding
    - OSRM for routing
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
    # GEOCODE START
    # --------------------------------------------------------

    start_location = geocode_location(
        start
    )

    # --------------------------------------------------------
    # GEOCODE DESTINATION
    # --------------------------------------------------------

    # If both locations are identical, don't make
    # a second Nominatim request.
    if start.lower() == destination.lower():

        destination_location = start_location

    else:

        destination_location = geocode_location(
            destination
        )

    # --------------------------------------------------------
    # OSRM COORDINATES
    # Format:
    # longitude,latitude;longitude,latitude
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

    # --------------------------------------------------------
    # OSRM RESPONSE
    # --------------------------------------------------------

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
    # OSRM:
    # [longitude, latitude]
    #
    # FOLIUM:
    # [latitude, longitude]
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
    # DISTANCE
    # --------------------------------------------------------

    distance_meters = float(
        route.get(
            "distance",
            0
        )
    )

    # --------------------------------------------------------
    # DURATION
    # --------------------------------------------------------

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
