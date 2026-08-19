import streamlit as st
import folium

from streamlit_folium import st_folium


def show_interactive_map(route):
    """
    Display an interactive OpenStreetMap map
    with the actual driving route.
    """

    if not route:
        st.info(
            "📍 Calculate a route first."
        )
        return

    # --------------------------------------------------------
    # START COORDINATES
    # --------------------------------------------------------

    start_lat = route[
        "start_latitude"
    ]

    start_lon = route[
        "start_longitude"
    ]

    # --------------------------------------------------------
    # DESTINATION COORDINATES
    # --------------------------------------------------------

    destination_lat = route[
        "destination_latitude"
    ]

    destination_lon = route[
        "destination_longitude"
    ]

    # --------------------------------------------------------
    # ROUTE POINTS
    # --------------------------------------------------------

    route_points = route.get(
        "route_points",
        []
    )

    # --------------------------------------------------------
    # MAP CENTER
    # --------------------------------------------------------

    center_lat = (
        start_lat +
        destination_lat
    ) / 2

    center_lon = (
        start_lon +
        destination_lon
    ) / 2

    # --------------------------------------------------------
    # CREATE MAP
    # --------------------------------------------------------

    travel_map = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=8,
        tiles="OpenStreetMap"
    )

    # --------------------------------------------------------
    # START MARKER
    # --------------------------------------------------------

    folium.Marker(
        [
            start_lat,
            start_lon
        ],
        tooltip="📍 Starting Location",
        popup=route.get(
            "start",
            "Start"
        )
    ).add_to(travel_map)

    # --------------------------------------------------------
    # DESTINATION MARKER
    # --------------------------------------------------------

    folium.Marker(
        [
            destination_lat,
            destination_lon
        ],
        tooltip="🏁 Destination",
        popup=route.get(
            "destination",
            "Destination"
        )
    ).add_to(travel_map)

    # --------------------------------------------------------
    # ACTUAL ROAD ROUTE
    # --------------------------------------------------------

    if route_points:

        folium.PolyLine(
            route_points,
            weight=6,
            opacity=0.9,
            tooltip="🚗 Driving Route"
        ).add_to(travel_map)

        # Automatically fit map
        # to the complete route.

        travel_map.fit_bounds(
            route_points
        )

    # --------------------------------------------------------
    # DISPLAY MAP
    # --------------------------------------------------------

    st_folium(
        travel_map,
        width=None,
        height=550
    )
