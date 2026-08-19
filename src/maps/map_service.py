import streamlit as st


def show_route_map(route):
    """
    Display a simple route summary on the Streamlit UI.

    The actual interactive map can be connected later
    without changing the routing logic.
    """

    if not route:
        st.info("📍 Calculate a route first.")
        return

    start = route.get("start", "Start")
    destination = route.get(
        "destination",
        "Destination"
    )

    distance = route.get(
        "distance_km",
        0
    )

    duration = route.get(
        "duration_minutes",
        0
    )

    hours = int(duration // 60)
    minutes = int(duration % 60)

    st.markdown("### 🗺️ Your Route")

    st.markdown(
        f"""
        **📍 {start}**

        ↓ 🚗

        **🌍 {destination}**

        ---
        
        📏 **Distance:** {distance} km  
        ⏱️ **Estimated driving time:** {hours}h {minutes}m
        """
    )
