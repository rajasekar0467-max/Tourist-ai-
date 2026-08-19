def calculate_fuel_cost(
    distance_km: float,
    mileage_kmpl: float,
    fuel_price: float,
    round_trip: bool = False
):
    """
    Calculate fuel requirement and estimated fuel cost.

    distance_km: One-way distance in kilometres
    mileage_kmpl: Vehicle mileage in km per litre
    fuel_price: Fuel price per litre
    round_trip: Whether to calculate return journey too
    """

    if distance_km <= 0:
        raise ValueError("Distance must be greater than 0.")

    if mileage_kmpl <= 0:
        raise ValueError("Mileage must be greater than 0.")

    if fuel_price < 0:
        raise ValueError("Fuel price cannot be negative.")

    total_distance = distance_km

    if round_trip:
        total_distance = distance_km * 2

    fuel_required = total_distance / mileage_kmpl
    estimated_cost = fuel_required * fuel_price

    return {
        "distance_km": round(total_distance, 2),
        "fuel_required_litres": round(fuel_required, 2),
        "estimated_fuel_cost": round(estimated_cost, 2)
    }
