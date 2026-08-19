import streamlit as st
import folium
from streamlit_folium import st_folium


def show_interactive_map(route):
    """
    Display an interactive OpenStreetMap map
    with start and destination markers.
    """

    if not route:
        st.info("📍 Calculate a route first.")
        return

    start_lat = route["start_latitude"]
    start_lon = route["start_longitude"]

    destination_lat = route[
        "destination_latitude"
    ]
    destination_lon = route[
        "destination_longitude"
    ]

    start_name = route.get(
        "start",
        "Start"
    )

    destination_name = route.get(
        "destination",
        "Destination"
    )

    center_lat = (
        start_lat + destination_lat
    ) / 2

    center_lon = (
        start_lon + destination_lon
    ) / 2

    travel_map = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=7,
        tiles="OpenStreetMap"
    )

    folium.Marker(
        [start_lat, start_lon],
        tooltip="Starting Location",
        popup=start_name,
        icon=folium.Icon(
            icon="play"
        )
    ).add_to(travel_map)

    folium.Marker(
        [destination_lat, destination_lon],
        tooltip="Destination",
        popup=destination_name,
        icon=folium.Icon(
            icon="flag"
        )
    ).add_to(travel_map)

    # Straight visual connection between
    # the two locations.
    # Actual road geometry will be added later.
    folium.PolyLine(
        [
            [start_lat, start_lon],
            [destination_lat, destination_lon]
        ],
        weight=5
    ).add_to(travel_map)

    st_folium(
        travel_map,
        width=None,
        height=500
    )
