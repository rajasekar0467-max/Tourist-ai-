def calculate_trip_budget(
    total_budget: float,
    travel_cost: float = 0,
    stay_cost: float = 0,
    food_cost: float = 0,
    activity_cost: float = 0,
    other_cost: float = 0
):
    """
    Calculate total estimated trip cost
    and remaining budget.
    """

    costs = {
        "travel": max(travel_cost, 0),
        "stay": max(stay_cost, 0),
        "food": max(food_cost, 0),
        "activities": max(activity_cost, 0),
        "other": max(other_cost, 0),
    }

    total_cost = sum(costs.values())
    remaining_budget = total_budget - total_cost

    return {
        "total_budget": round(total_budget, 2),
        "travel_cost": round(costs["travel"], 2),
        "stay_cost": round(costs["stay"], 2),
        "food_cost": round(costs["food"], 2),
        "activity_cost": round(costs["activities"], 2),
        "other_cost": round(costs["other"], 2),
        "total_cost": round(total_cost, 2),
        "remaining_budget": round(remaining_budget, 2),
        "within_budget": remaining_budget >= 0,
    }
