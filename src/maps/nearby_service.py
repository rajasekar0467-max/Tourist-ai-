import requests
import math


OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter"
]


def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    radius = 6371

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1

    a = (
        math.sin(lat_diff / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(lon_diff / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


def get_overpass_data(query):
    """
    Try multiple public Overpass servers.
    Uses query parameter instead of raw POST body
    to avoid common 406 errors.
    """

    headers = {
        "User-Agent": (
            "TouristAI/1.0 "
            "(Travel Planning Application)"
        ),
        "Accept": "application/json"
    }

    last_error = None

    for server in OVERPASS_SERVERS:

        try:

            response = requests.get(
                server,
                params={
                    "data": query
                },
                headers=headers,
                timeout=45
            )

            response.raise_for_status()

            return response.json()

        except Exception as error:

            last_error = error
            continue

    raise RuntimeError(
        f"Nearby search server unavailable: {last_error}"
    )


def get_nearby_places(
    latitude,
    longitude,
    place_type="restaurant",
    radius=5000,
    limit=12
):

    latitude = float(latitude)
    longitude = float(longitude)
    radius = int(radius)

    place_type = str(
        place_type
    ).lower().strip()

    filters = {

        "restaurant": """
        ["amenity"="restaurant"]
        """,

        "hotel": """
        ["tourism"~"hotel|guest_house|hostel|motel"]
        """,

        "cafe": """
        ["amenity"="cafe"]
        """,

        "food": """
        ["amenity"~"restaurant|fast_food|food_court|cafe"]
        """
    }

    query_filter = filters.get(
        place_type,
        filters["restaurant"]
    )

    query = f"""
[out:json][timeout:30];

(
    nwr
    {query_filter}
    (around:{radius},{latitude},{longitude});
);

out center tags;
"""

    data = get_overpass_data(
        query
    )

    places = []

    for item in data.get(
        "elements",
        []
    ):

        tags = item.get(
            "tags",
            {}
        )

        name = tags.get(
            "name"
        )

        if not name:
            continue

        place_lat = item.get(
            "lat"
        )

        place_lon = item.get(
            "lon"
        )

        if (
            place_lat is None
            or place_lon is None
        ):

            center = item.get(
                "center",
                {}
            )

            place_lat = center.get(
                "lat"
            )

            place_lon = center.get(
                "lon"
            )

        if (
            place_lat is None
            or place_lon is None
        ):
            continue

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            place_lat,
            place_lon
        )

        address_parts = [

            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:city")
        ]

        address = ", ".join(
            str(part)
            for part in address_parts
            if part
        )

        if not address:

            address = (
                tags.get("addr:full")
                or tags.get("addr:place")
                or tags.get("addr:district")
                or "Address not available"
            )

        places.append(
            {
                "name": name,
                "latitude": float(place_lat),
                "longitude": float(place_lon),

                "distance_km": round(
                    distance_km,
                    2
                ),

                "address": address,

                "category": (
                    tags.get("amenity")
                    or tags.get("tourism")
                    or place_type
                )
            }
        )

    places.sort(
        key=lambda item:
        item["distance_km"]
    )

    return places[:int(limit)]


def create_google_maps_place_url(
    latitude,
    longitude,
    name=""
):

    query = (
        f"{latitude},{longitude}"
    )

    if name:
        query = (
            f"{name} {latitude},{longitude}"
        )

    return (
        "https://www.google.com/maps/search/"
        f"?api=1&query={requests.utils.quote(query)}"
    )
