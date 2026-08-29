import requests
from urllib.parse import quote
import time


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


HEADERS = {
    "User-Agent": "TouristAI/1.0"
}


def get_coordinates(place: str):
    """
    Get latitude and longitude from a place name.
    """

    if not place or not place.strip():
        raise ValueError("Location cannot be empty")

    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code == 429:
            raise Exception(
                "Location service is busy. Please wait a moment and try again."
            )

        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError(
                f"Location not found: {place}"
            )

        latitude = float(data[0]["lat"])
        longitude = float(data[0]["lon"])

        return latitude, longitude

    except requests.exceptions.Timeout:
        raise Exception(
            "Location service timeout. Please try again."
        )

    except requests.exceptions.RequestException as e:
        raise Exception(
            f"Location service error: {str(e)}"
        )


def get_route_distance(start: str, destination: str):
    """
    Get driving route distance and duration.
    """

    start_lat, start_lon = get_coordinates(start)

    # Small delay to respect Nominatim usage policy
    time.sleep(1.1)

    dest_lat, dest_lon = get_coordinates(destination)

    coordinates = (
        f"{start_lon},{start_lat};"
        f"{dest_lon},{dest_lat}"
    )

    url = f"{OSRM_URL}/{coordinates}"

    params = {
        "overview": "false",
        "alternatives": "false",
        "steps": "false"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            raise Exception(
                "Unable to calculate route."
            )

        route = data["routes"][0]

        distance_km = round(
            route["distance"] / 1000,
            2
        )

        duration_minutes = round(
            route["duration"] / 60,
            1
        )

        return {
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "duration_hours": round(
                duration_minutes / 60,
                2
            )
        }

    except requests.exceptions.Timeout:
        raise Exception(
            "Route calculation timeout. Please try again."
        )

    except requests.exceptions.RequestException as e:
        raise Exception(
            f"Route service error: {str(e)}"
        )


def calculate_fuel_cost(
    distance_km: float,
    mileage_kmpl: float,
    fuel_price: float,
    round_trip: bool = True
):
    """
    Calculate required fuel and estimated cost.
    """

    distance_km = float(distance_km or 0)
    mileage_kmpl = float(mileage_kmpl or 0)
    fuel_price = float(fuel_price or 0)

    if distance_km <= 0:
        raise ValueError(
            "Distance must be greater than zero."
        )

    if mileage_kmpl <= 0:
        raise ValueError(
            "Mileage must be greater than zero."
        )

    if fuel_price <= 0:
        raise ValueError(
            "Fuel price must be greater than zero."
        )

    total_distance = distance_km

    if round_trip:
        total_distance = distance_km * 2

    fuel_required = total_distance / mileage_kmpl
    total_cost = fuel_required * fuel_price

    return {
        "one_way_distance": round(distance_km, 2),
        "total_distance": round(total_distance, 2),
        "fuel_required": round(fuel_required, 2),
        "fuel_cost": round(total_cost, 2)
    }
