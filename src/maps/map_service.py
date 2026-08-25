import streamlit as st
import folium

from streamlit_folium import st_folium


def show_interactive_map(route):
    """
    Display an interactive OpenStreetMap map
    with the calculated driving route.
    """

    if not route:

        st.info(
            "📍 Calculate a route first."
        )

        return

    # ========================================================
    # COORDINATES
    # ========================================================

    start_lat = route.get(
        "start_latitude"
    )

    start_lon = route.get(
        "start_longitude"
    )

    destination_lat = route.get(
        "destination_latitude"
    )

    destination_lon = route.get(
        "destination_longitude"
    )

    if None in [
        start_lat,
        start_lon,
        destination_lat,
        destination_lon
    ]:

        st.warning(
            "Route coordinates are unavailable."
        )

        return

    route_points = route.get(
        "route_points",
        []
    )

    # ========================================================
    # MAP CENTER
    # ========================================================

    center_lat = (
        start_lat +
        destination_lat
    ) / 2

    center_lon = (
        start_lon +
        destination_lon
    ) / 2

    # ========================================================
    # CREATE MAP
    # ========================================================

    travel_map = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=8,
        tiles="OpenStreetMap",
        control_scale=True
    )

    # ========================================================
    # START MARKER
    # ========================================================

    folium.Marker(
        location=[
            start_lat,
            start_lon
        ],

        popup=folium.Popup(
            f"""
            <b>📍 Starting Location</b>
            <br>
            {route.get(
                'start_display_name',
                route.get('start', 'Start')
            )}
            """,
            max_width=300
        ),

        tooltip="📍 Starting Location",

        icon=folium.Icon(
            icon="play",
            prefix="fa"
        )

    ).add_to(
        travel_map
    )

    # ========================================================
    # DESTINATION MARKER
    # ========================================================

    folium.Marker(
        location=[
            destination_lat,
            destination_lon
        ],

        popup=folium.Popup(
            f"""
            <b>🏁 Destination</b>
            <br>
            {route.get(
                'destination_display_name',
                route.get(
                    'destination',
                    'Destination'
                )
            )}
            """,
            max_width=300
        ),

        tooltip="🏁 Destination",

        icon=folium.Icon(
            icon="flag",
            prefix="fa"
        )

    ).add_to(
        travel_map
    )

    # ========================================================
    # ROUTE LINE
    # ========================================================

    if route_points:

        folium.PolyLine(
            locations=route_points,
            weight=6,
            opacity=0.9,
            tooltip="🚗 Driving Route"
        ).add_to(
            travel_map
        )

        # Automatically fit the full route
        travel_map.fit_bounds(
            route_points
        )

    else:

        # If route points unavailable,
        # fit start and destination.

        travel_map.fit_bounds(
            [
                [start_lat, start_lon],
                [
                    destination_lat,
                    destination_lon
                ]
            ]
        )

    # ========================================================
    # DISPLAY MAP
    # ========================================================

    st_folium(
        travel_map,
        width=None,
        height=550,
        key="tourist_route_map"
    )
