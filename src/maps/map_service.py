import streamlit as st
import folium

from streamlit_folium import st_folium
from urllib.parse import quote


# ============================================================
# GOOGLE MAPS URL
# ============================================================

def get_google_maps_url(route):
    """
    Create Google Maps directions URL.

    Opens the route from starting location
    to destination.
    """

    if not route:
        return None

    start = route.get("start", "")
    destination = route.get("destination", "")

    if not start or not destination:
        return None

    start_encoded = quote(start)
    destination_encoded = quote(destination)

    return (
        "https://www.google.com/maps/dir/"
        f"{start_encoded}/"
        f"{destination_encoded}"
    )


# ============================================================
# GOOGLE MAPS DRIVE NAVIGATION URL
# ============================================================

def get_google_maps_drive_url(route):
    """
    Create Google Maps driving navigation URL.

    On mobile, this can open Google Maps
    with driving mode.
    """

    if not route:
        return None

    start_lat = route.get("start_latitude")
    start_lon = route.get("start_longitude")

    destination_lat = route.get(
        "destination_latitude"
    )

    destination_lon = route.get(
        "destination_longitude"
    )

    if (
        start_lat is None
        or start_lon is None
        or destination_lat is None
        or destination_lon is None
    ):
        return None

    origin = f"{start_lat},{start_lon}"

    destination = (
        f"{destination_lat},"
        f"{destination_lon}"
    )

    return (
        "https://www.google.com/maps/dir/"
        f"?api=1"
        f"&origin={quote(origin)}"
        f"&destination={quote(destination)}"
        f"&travelmode=driving"
    )


# ============================================================
# OPEN GOOGLE MAPS BUTTONS
# ============================================================

def show_google_maps_buttons(route):
    """
    Display Google Maps route and
    driving navigation buttons.
    """

    if not route:
        return

    maps_url = get_google_maps_url(route)

    drive_url = get_google_maps_drive_url(
        route
    )

    col1, col2 = st.columns(2)

    with col1:

        if maps_url:

            st.link_button(
                "🗺️ Open in Google Maps",
                maps_url,
                use_container_width=True
            )

    with col2:

        if drive_url:

            st.link_button(
                "🚗 Start Driving Navigation",
                drive_url,
                use_container_width=True
            )


# ============================================================
# SHOW INTERACTIVE MAP
# ============================================================

def show_interactive_map(route):
    """
    Display an interactive OpenStreetMap map
    with actual driving route.
    """

    if not route:

        st.info(
            "📍 Calculate a route first."
        )

        return

    # --------------------------------------------------------
    # START COORDINATES
    # --------------------------------------------------------

    start_lat = route.get(
        "start_latitude"
    )

    start_lon = route.get(
        "start_longitude"
    )

    # --------------------------------------------------------
    # DESTINATION COORDINATES
    # --------------------------------------------------------

    destination_lat = route.get(
        "destination_latitude"
    )

    destination_lon = route.get(
        "destination_longitude"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    coordinates = [
        start_lat,
        start_lon,
        destination_lat,
        destination_lon
    ]

    if any(
        value is None
        for value in coordinates
    ):

        st.warning(
            "Route coordinates are unavailable."
        )

        return

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
        tiles="OpenStreetMap",
        control_scale=True
    )

    # --------------------------------------------------------
    # START MARKER
    # --------------------------------------------------------

    folium.Marker(
        [
            start_lat,
            start_lon
        ],

        tooltip=(
            f"📍 Start: "
            f"{route.get('start', 'Starting Location')}"
        ),

        popup=folium.Popup(
            f"""
            <b>📍 Starting Location</b>
            <br>
            {route.get('start', 'Start')}
            """,
            max_width=250
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

        tooltip=(
            f"🏁 Destination: "
            f"{route.get('destination', 'Destination')}"
        ),

        popup=folium.Popup(
            f"""
            <b>🏁 Destination</b>
            <br>
            {route.get('destination', 'Destination')}
            """,
            max_width=250
        )

    ).add_to(travel_map)

    # --------------------------------------------------------
    # ACTUAL DRIVING ROUTE
    # --------------------------------------------------------

    if route_points:

        folium.PolyLine(
            route_points,
            weight=6,
            opacity=0.9,
            tooltip="🚗 Actual Driving Route"
        ).add_to(travel_map)

        travel_map.fit_bounds(
            route_points,
            padding=(30, 30)
        )

    else:

        travel_map.fit_bounds(
            [
                [
                    start_lat,
                    start_lon
                ],
                [
                    destination_lat,
                    destination_lon
                ]
            ],
            padding=(30, 30)
        )

    # --------------------------------------------------------
    # DISPLAY MAP
    # --------------------------------------------------------

    st_folium(
        travel_map,
        width=None,
        height=550,
        key="tourist_route_map")
    )
