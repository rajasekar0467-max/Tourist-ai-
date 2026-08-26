import requests
import math
import time


# Multiple Overpass servers for fallback
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter"
]


def calculate_distance_km(lat1, lon1, lat2, lon2):

    radius = 6371.0

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1

    a = (
        math.sin(lat_diff / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(lon_diff / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


def get_query_filter(place_type):

    place_type = str(place_type).lower().strip()

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

    return filters.get(
        place_type,
        filters["restaurant"]
    )


def request_overpass(query):

    headers = {
        "User-Agent": (
            "TouristAI/1.0 "
            "Travel-Planning-App"
        ),
        "Accept": "application/json"
    }

    last_error = None

    for server in OVERPASS_SERVERS:

        try:

            response = requests.post(
                server,
                data={
                    "data": query
                },
                headers=headers,
                timeout=45
            )

            response.raise_for_status()

            data = response.json()

            return data

        except Exception as error:

            last_error = error

            # Small delay before trying backup server
            time.sleep(1)

    raise RuntimeError(
        f"Nearby place servers unavailable: {last_error}"
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

    # Safety limits
    radius = max(
        500,
        min(radius, 20000)
    )

    limit = max(
        1,
        min(int(limit), 30)
    )

    query_filter = get_query_filter(
        place_type
    )

    # Proper Overpass QL query
    query = f"""
[out:json][timeout:30];

(
  node{query_filter}
  (around:{radius},{latitude},{longitude});

  way{query_filter}
  (around:{radius},{latitude},{longitude});

  relation{query_filter}
  (around:{radius},{latitude},{longitude});
);

out center tags;
"""

    data = request_overpass(
        query
    )

    places = []

    seen = set()

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

        # Get coordinates
        if item.get("type") == "node":

            place_lat = item.get("lat")
            place_lon = item.get("lon")

        else:

            center = item.get(
                "center",
                {}
            )

            place_lat = center.get("lat")
            place_lon = center.get("lon")

        if (
            place_lat is None
            or place_lon is None
        ):
            continue

        place_lat = float(place_lat)
        place_lon = float(place_lon)

        # Avoid duplicates
        unique_key = (
            name.lower(),
            round(place_lat, 5),
            round(place_lon, 5)
        )

        if unique_key in seen:
            continue

        seen.add(unique_key)

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            place_lat,
            place_lon
        )

        # Build address
        address_parts = []

        for key in [
            "addr:housenumber",
            "addr:street",
            "addr:suburb",
            "addr:city"
        ]:

            value = tags.get(key)

            if value:
                address_parts.append(
                    str(value)
                )

        address = ", ".join(
            address_parts
        )

        if not address:

            address = (
                tags.get("addr:full")
                or tags.get("addr:place")
                or tags.get("city")
                or "Address not available"
            )

        category = (
            tags.get("amenity")
            or tags.get("tourism")
            or place_type
        )

        places.append(
            {
                "name": name,
                "latitude": place_lat,
                "longitude": place_lon,
                "distance_km": round(
                    distance_km,
                    2
                ),
                "address": address,
                "category": category
            }
        )

    # Sort nearest first
    places.sort(
        key=lambda place:
        place["distance_km"]
    )

    return places[:limit]


def create_google_maps_place_url(
    latitude,
    longitude,
    place_name=None
):

    latitude = float(latitude)
    longitude = float(longitude)

    if place_name:

        query = requests.utils.quote(
            f"{place_name} {latitude},{longitude}"
        )

        return (
            "https://www.google.com/maps/search/"
            f"?api=1&query={query}"
        )

    return (
        "https://www.google.com/maps/search/"
        f"?api=1&query={latitude},{longitude}"
    )
