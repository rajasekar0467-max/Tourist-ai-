import requests
import math


OVERPASS_URL = (
    "https://overpass-api.de/api/interpreter"
)


def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    radius = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

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

    c = (
        2
        *
        math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )
    )

    return radius * c


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

    place_type = place_type.lower()

    if place_type == "hotel":

        query_filter = """
        ["tourism"~"hotel|guest_house|hostel|motel"]
        """

    elif place_type == "cafe":

        query_filter = """
        ["amenity"="cafe"]
        """

    elif place_type == "food":

        query_filter = """
        ["amenity"~"restaurant|fast_food|food_court|cafe"]
        """

    else:

        query_filter = """
        ["amenity"="restaurant"]
        """

    query = f"""
    [out:json][timeout:25];

    (
        node
        {query_filter}
        (around:{radius},{latitude},{longitude});

        way
        {query_filter}
        (around:{radius},{latitude},{longitude});

        relation
        {query_filter}
        (around:{radius},{latitude},{longitude});
    );

    out center tags;
    """

    response = requests.post(
        OVERPASS_URL,
        data=query,
        timeout=35
    )

    response.raise_for_status()

    data = response.json()

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
                or "Address not available"
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

    return places[:limit]


def create_google_maps_place_url(
    latitude,
    longitude
):

    return (
        "https://www.google.com/maps/search/"
        f"?api=1&query={latitude},{longitude}"
    )
