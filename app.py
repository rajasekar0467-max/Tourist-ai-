import streamlit as st
import time
import requests
import base64

from src.voice_component import voice_assistant_component

from src.ai.groq_service import (
    ask_tourist_ai,
    ask_general_ai
)

from src.travel.fuel_calculator import (
    calculate_fuel_cost
)

from src.maps.distance_service import (
    get_route_distance
)

from src.maps.map_service import (
    show_interactive_map
)

from src.maps.nearby_service import (
    get_nearby_places,
    create_google_maps_place_url
)

from src.budget.budget_calculator import (
    calculate_trip_budget
)

from src.camera.camera_service import (
    prepare_image_for_vision
)

from src.camera.vision_service import (
    analyze_prepared_image
)

from src.weather.weather_service import (
    get_weather,
    weather_description,
    get_weather_advice
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Tourist AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {

    "page_mode": "tourist",

    "chat_history": [],
    "general_chat_history": [],
    "friday_history": [],

    "route": None,
    "fuel": None,
    "weather": None,
    "weather_advice": "",

    "nearby_places": [],

    "budget_result": None,

    "camera_analysis": None,

    "friday_status": "READY TO LISTEN",
    "friday_last_answer": "",
    "friday_audio": "",
    "friday_running": False,
    "friday_last_event": "",

    "complete_trip_plan": ""
}


for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# NEW CHAT
# ============================================================

def new_chat():

    st.session_state.chat_history = []
    st.session_state.general_chat_history = []
    st.session_state.friday_history = []

    st.session_state.route = None
    st.session_state.fuel = None
    st.session_state.weather = None
    st.session_state.weather_advice = ""

    st.session_state.nearby_places = []

    st.session_state.budget_result = None

    st.session_state.camera_analysis = None

    st.session_state.friday_status = "READY TO LISTEN"
    st.session_state.friday_last_answer = ""
    st.session_state.friday_audio = ""
    st.session_state.friday_running = False
    st.session_state.friday_last_event = ""

    st.session_state.complete_trip_plan = ""

    st.rerun()


# ============================================================
# FRIDAY VOICE
# ============================================================

def generate_friday_voice(text):

    if not text:
        return ""

    try:

        api_key = st.secrets.get(
            "ELEVENLABS_API_KEY",
            ""
        )

        voice_id = st.secrets.get(
            "ELEVENLABS_VOICE_ID",
            ""
        )

        # ElevenLabs not configured
        # Voice component can still handle browser voice
        if not api_key or not voice_id:
            return ""

        url = (
            "https://api.elevenlabs.io/"
            f"v1/text-to-speech/{voice_id}"
        )

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }

        payload = {
            "text": str(text)[:2500],

            "model_id":
                "eleven_multilingual_v2",

            "voice_settings": {

                "stability": 0.45,

                "similarity_boost": 0.75,

                "style": 0.30,

                "use_speaker_boost": True
            }
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60
        )

        response.raise_for_status()

        return base64.b64encode(
            response.content
        ).decode()

    except Exception:

        return ""


# ============================================================
# FRIDAY AI
# ============================================================

def ask_friday(user_message):

    prompt = f"""
You are FRIDAY, an intelligent personal voice assistant.

Personality:
Warm, calm, intelligent, friendly and natural.

Language:
Understand Tamil, English and Tanglish.
Reply naturally in the user's style.

Rules:
Keep answers conversational.
Do not sound robotic.
Do not use unnecessary long answers.
Be helpful and friendly.

User message:
{user_message}
"""

    # Keep only recent history
    recent_history = (
        st.session_state.friday_history[-4:]
    )

    return ask_general_ai(

        prompt,

        voice="FRIDAY",

        language="Tamil + English",

        chat_history=recent_history
    )


# ============================================================
# TYPING EFFECT
# ============================================================

def type_response(answer):

    placeholder = st.empty()

    displayed = ""

    for character in str(answer):

        displayed += character

        placeholder.markdown(
            displayed + "▌"
        )

        time.sleep(0.001)

    placeholder.markdown(
        displayed
    )


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_number(value, default=0):

    try:

        return float(value)

    except Exception:

        return default


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    #MainMenu,
    footer,
    header {
        visibility: hidden;
    }

    .stApp {

        background:

            radial-gradient(
                circle at top,
                #10251f 0%,
                #08110f 45%,
                #050807 100%
            );

        color: white;
    }


    .block-container {

        max-width: 1150px;

        padding-top: 1rem;

        padding-bottom: 5rem;
    }


    .stApp,
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown div,
    .stMarkdown li,
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    label {

        color:
            #f8fafc !important;
    }


    .stButton button {

        background:
            rgba(18, 35, 30, 0.92) !important;

        color:
            white !important;

        border:
            1px solid #245c4a !important;

        border-radius:
            14px !important;

        min-height:
            48px;

        font-size:
            16px;

        font-weight:
            600;

        transition:
            0.25s;
    }


    .stButton button:hover {

        border-color:
            #20d489 !important;

        box-shadow:
            0 0 18px
            rgba(32, 212, 137, 0.35);

        transform:
            translateY(-1px);
    }


    .stLinkButton a {

        background:
            #123c30 !important;

        color:
            white !important;

        border:
            1px solid #20d489 !important;

        border-radius:
            14px !important;
    }


    input,
    textarea {

        background:
            #0c1815 !important;

        color:
            white !important;

        border-radius:
            10px !important;
    }


    div[data-testid="stMetric"] {

        background:
            rgba(15, 35, 29, 0.85);

        padding:
            16px;

        border-radius:
            14px;

        border:
            1px solid #214c3d;
    }


    .stAlert {

        border-radius:
            14px;
    }


    </style>
    """,

    unsafe_allow_html=True
)


# ============================================================
# NAVIGATION
# ============================================================

n1, n2, n3, n4 = st.columns(4)


with n1:

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        new_chat()


with n2:

    if st.button(
        "🌍 Tourist AI",
        use_container_width=True
    ):

        st.session_state.page_mode = "tourist"

        st.session_state.friday_running = False

        st.rerun()


with n3:

    if st.button(
        "💬 Chat Mode",
        use_container_width=True
    ):

        st.session_state.page_mode = "chat"

        st.session_state.friday_running = False

        st.rerun()


with n4:

    if st.button(
        "🎙️ FRIDAY",
        use_container_width=True
    ):

        st.session_state.page_mode = "friday"

        st.rerun()


# ============================================================
# FRIDAY VOICE MODE
# ============================================================

# ============================================================
# FRIDAY CONTINUOUS VOICE MODE
# ============================================================

if st.session_state.page_mode == "friday":

    st.title("🎙️ FRIDAY")

    st.caption(
        "Continuous intelligent voice companion"
    )

    st.divider()


    component_result = voice_assistant_component(

        running=st.session_state.friday_running,

        language="ta-IN",

        audio_b64=st.session_state.friday_audio,

        status=st.session_state.friday_status,

        key="friday_voice_component"

    )


    # ========================================================
    # RECEIVE VOICE FROM BROWSER
    # ========================================================

    if component_result:

        component_running = component_result.get(
            "running",
            False
        )


        # Sync running state
        if component_running != st.session_state.friday_running:

            st.session_state.friday_running = bool(
                component_running
            )


        user_text = str(
            component_result.get(
                "text",
                ""
            )
        ).strip()


        event_id = str(
            component_result.get(
                "event_id",
                ""
            )
        )


        # ====================================================
        # NEW VOICE MESSAGE
        # ====================================================

        if (

            user_text

            and

            event_id

            and

            event_id
            !=
            st.session_state.friday_last_event

        ):

            st.session_state.friday_last_event = (
                event_id
            )


            st.session_state.friday_status = (
                "THINKING..."
            )


            # Clear previous audio before processing
            st.session_state.friday_audio = ""


            try:

                answer = ask_friday(
                    user_text
                )


                # Save memory
                st.session_state.friday_history.append(
                    {
                        "user": user_text,
                        "assistant": answer
                    }
                )


                # Keep memory small
                st.session_state.friday_history = (
                    st.session_state.friday_history[-8:]
                )


                st.session_state.friday_last_answer = (
                    answer
                )


                st.session_state.friday_status = (
                    "FRIDAY IS SPEAKING..."
                )


                # =================================================
                # ELEVENLABS AUDIO
                # =================================================

                audio = generate_friday_voice(
                    answer
                )


                if audio:

                    st.session_state.friday_audio = (
                        audio
                    )

                else:

                    # No ElevenLabs audio
                    # Component will continue listening
                    st.session_state.friday_status = (
                        "READY TO LISTEN"
                    )


                st.rerun()


            except Exception as error:

                st.session_state.friday_status = (
                    "READY TO LISTEN"
                )


                st.session_state.friday_audio = ""


                st.error(
                    f"FRIDAY Error: {error}"
                )


    st.divider()


    st.caption(
        "💚 Continuous Voice Mode • "
        "Start once and FRIDAY keeps listening until you stop."
    )


    if st.button(
        "🗑️ Clear FRIDAY Memory",
        use_container_width=True
    ):

        st.session_state.friday_history = []

        st.session_state.friday_last_answer = ""

        st.session_state.friday_last_event = ""

        st.success(
            "FRIDAY memory cleared."
        )


# ============================================================
# NORMAL CHAT MODE
# ============================================================

elif st.session_state.page_mode == "chat":

    st.title("💬 AI Chat")

    st.caption(
        "Tamil • English • Tanglish"
    )


    for chat in (
        st.session_state.general_chat_history
    ):

        with st.chat_message("user"):

            st.markdown(
                chat["user"]
            )


        with st.chat_message("assistant"):

            st.markdown(
                chat["assistant"]
            )


    user_message = st.chat_input(
        "Message AI..."
    )


    if user_message:

        with st.chat_message("user"):

            st.markdown(
                user_message
            )


        try:

            answer = ask_general_ai(

                user_message,

                voice="FRIDAY",

                language="Tamil + English",

                chat_history=
                    st.session_state
                    .general_chat_history[-6:]
            )


            with st.chat_message("assistant"):

                type_response(
                    answer
                )


            st.session_state.general_chat_history.append(
                {
                    "user": user_message,
                    "assistant": answer
                }
            )


        except Exception as error:

            st.error(
                f"AI Error: {error}"
            )


# ============================================================
# TOURIST AI
# ============================================================

else:

    st.title("🌍 Tourist AI")

    st.caption(
        "Plan • Explore • Discover • Travel Smarter"
    )


    # ========================================================
    # TRIP DETAILS
    # ========================================================

    st.divider()

    st.subheader(
        "✈️ Plan Your Trip"
    )


    c1, c2 = st.columns(2)


    with c1:

        start_location = st.text_input(
            "📍 Starting Location",
            placeholder="Madurai"
        )


    with c2:

        destination = st.text_input(
            "🌍 Destination",
            placeholder="Ooty"
        )


    c3, c4, c5 = st.columns(3)


    with c3:

        days = st.number_input(
            "📅 Days",
            min_value=1,
            value=2,
            step=1
        )


    with c4:

        people = st.number_input(
            "👥 People",
            min_value=1,
            value=2,
            step=1
        )


    with c5:

        budget = st.number_input(
            "💰 Total Budget ₹",
            min_value=0.0,
            value=10000.0,
            step=500.0
        )


    # ========================================================
    # FUEL
    # ========================================================

    st.divider()

    st.subheader(
        "🚗 Travel & Fuel"
    )


    f1, f2, f3 = st.columns(3)


    with f1:

        fuel_type = st.selectbox(
            "Fuel Type",
            ["Petrol", "Diesel"]
        )


    with f2:

        mileage = st.number_input(
            "Mileage (km/L)",
            min_value=1.0,
            value=15.0,
            step=1.0
        )


    with f3:

        fuel_price = st.number_input(
            "Fuel Price ₹/L",
            min_value=0.0,
            value=100.0,
            step=1.0
        )


    # ========================================================
    # CALCULATE ROUTE
    # ========================================================

    if st.button(
        "📍 Calculate Route & Fuel",
        use_container_width=True
    ):

        if (
            not start_location.strip()
            or not destination.strip()
        ):

            st.warning(
                "Please enter starting location and destination."
            )

        else:

            try:

                with st.spinner(
                    "Calculating route..."
                ):

                    route = get_route_distance(
                        start_location,
                        destination
                    )


                    st.session_state.route = route


                    fuel = calculate_fuel_cost(

                        safe_number(
                            route.get(
                                "distance_km",
                                0
                            )
                        ),

                        safe_number(
                            mileage
                        ),

                        safe_number(
                            fuel_price
                        ),

                        round_trip=True
                    )


                    st.session_state.fuel = fuel


                    # Reset dependent results
                    st.session_state.weather = None

                    st.session_state.nearby_places = []


                st.success(
                    "Route calculated successfully!"
                )


            except Exception as error:

                st.error(
                    f"Route failed: {error}"
                )


    # ========================================================
    # ROUTE RESULT + GOOGLE MAP
    # ========================================================

    if st.session_state.route:

        route = st.session_state.route


        st.divider()

        st.subheader(
            "🗺️ Route Result"
        )


        distance = safe_number(
            route.get(
                "distance_km",
                0
            )
        )


        duration = safe_number(
            route.get(
                "duration_minutes",
                0
            )
        )


        r1, r2, r3 = st.columns(3)


        with r1:

            st.metric(
                "One-way Distance",
                f"{distance:.1f} km"
            )


        with r2:

            st.metric(
                "Round Trip",
                f"{distance * 2:.1f} km"
            )


        with r3:

            st.metric(
                "Driving Time",
                f"{int(duration // 60)}h "
                f"{int(duration % 60)}m"
            )


        # GOOGLE MAP DISPLAY
        try:

            show_interactive_map(
                route
            )

        except Exception as error:

            st.warning(
                f"Interactive map unavailable: {error}"
            )


        # GOOGLE MAP OPEN BUTTON
        google_maps_url = route.get(
            "google_maps_url",
            ""
        )


        if google_maps_url:

            st.link_button(
                "🗺️ Open in Google Maps",
                google_maps_url,
                use_container_width=True
            )

        else:

            st.warning(
                "Google Maps link not available."
            )


    # ========================================================
    # FUEL ESTIMATE
    # ========================================================

    if st.session_state.fuel:

        fuel = st.session_state.fuel


        st.divider()

        st.subheader(
            "⛽ Fuel Estimate"
        )


        fuel_litres = safe_number(
            fuel.get(
                "fuel_required_litres",
                fuel.get(
                    "fuel_required",
                    0
                )
            )
        )


        fuel_cost = safe_number(
            fuel.get(
                "estimated_fuel_cost",
                fuel.get(
                    "fuel_cost",
                    0
                )
            )
        )


        fu1, fu2, fu3 = st.columns(3)


        with fu1:

            st.metric(
                "Fuel Type",
                fuel_type
            )


        with fu2:

            st.metric(
                "Fuel Required",
                f"{fuel_litres:.2f} L"
            )


        with fu3:

            st.metric(
                "Estimated Fuel Cost",
                f"₹{fuel_cost:.2f}"
            )


    # ========================================================
    # WEATHER
    # ========================================================

    if st.session_state.route:

        st.divider()

        st.subheader(
            "🌤️ Destination Weather"
        )


        if st.button(
            "🌤️ Check Weather",
            use_container_width=True
        ):

            try:

                route = st.session_state.route


                latitude = safe_number(
                    route.get(
                        "destination_latitude"
                    )
                )


                longitude = safe_number(
                    route.get(
                        "destination_longitude"
                    )
                )


                if latitude == 0 or longitude == 0:

                    raise ValueError(
                        "Destination coordinates not found."
                    )


                with st.spinner(
                    "Checking weather..."
                ):

                    weather = get_weather(
                        latitude,
                        longitude
                    )


                st.session_state.weather = (
                    weather
                )


                try:

                    st.session_state.weather_advice = (
                        get_weather_advice(
                            weather
                        )
                    )

                except Exception:

                    st.session_state.weather_advice = ""


                st.success(
                    "Weather information loaded!"
                )


            except Exception as error:

                st.error(
                    f"Weather unavailable: {error}"
                )


        if st.session_state.weather:

            weather = st.session_state.weather


            w1, w2, w3, w4 = st.columns(4)


            with w1:

                st.metric(
                    "🌡️ Temperature",
                    f"{safe_number(weather.get('temperature')):.1f}°C"
                )


            with w2:

                st.metric(
                    "🤗 Feels Like",
                    f"{safe_number(weather.get('feels_like')):.1f}°C"
                )


            with w3:

                st.metric(
                    "💧 Humidity",
                    f"{safe_number(weather.get('humidity')):.0f}%"
                )


            with w4:

                st.metric(
                    "💨 Wind",
                    f"{safe_number(weather.get('wind_speed')):.1f} km/h"
                )


            try:

                description = weather_description(
                    weather.get(
                        "weather_code"
                    )
                )

                st.info(
                    f"🌤️ {description}"
                )

            except Exception:

                pass


            if st.session_state.weather_advice:

                st.success(
                    st.session_state.weather_advice
                )


    # ========================================================
    # NEARBY PLACES
    # ========================================================

    if st.session_state.route:

        st.divider()

        st.subheader(
            "📍 Nearby Places"
        )


        nearby_type = st.selectbox(

            "Find nearby",

            [
                "Tourist Attractions",
                "Restaurants",
                "Hotels",
                "Hospitals",
                "Petrol Stations",
                "Shopping"
            ]
        )


        if st.button(
            "🔎 Find Nearby Places",
            use_container_width=True
        ):

            try:

                route = st.session_state.route


                latitude = safe_number(
                    route.get(
                        "destination_latitude"
                    )
                )


                longitude = safe_number(
                    route.get(
                        "destination_longitude"
                    )
                )


                if latitude == 0 or longitude == 0:

                    raise ValueError(
                        "Destination coordinates not available."
                    )


                with st.spinner(
                    "Searching nearby places..."
                ):

                    places = get_nearby_places(
                        latitude,
                        longitude,
                        nearby_type
                    )


                st.session_state.nearby_places = (
                    places or []
                )


                if places:

                    st.success(
                        f"{len(places)} places found!"
                    )

                else:

                    st.info(
                        "No nearby places found."
                    )


            except Exception as error:

                st.error(
                    f"Nearby Search Unavailable: {error}"
                )


        if st.session_state.nearby_places:

            for index, place in enumerate(
                st.session_state.nearby_places
            ):

                if not isinstance(
                    place,
                    dict
                ):

                    st.write(
                        f"📍 {place}"
                    )

                    continue


                name = place.get(
                    "name",
                    place.get(
                        "display_name",
                        "Unknown Place"
                    )
                )


                address = place.get(
                    "address",
                    ""
                )


                place_lat = place.get(
                    "latitude",
                    place.get(
                        "lat"
                    )
                )


                place_lon = place.get(
                    "longitude",
                    place.get(
                        "lon"
                    )
                )


                st.markdown(
                    f"### 📍 {name}"
                )


                if address:

                    st.caption(
                        str(address)
                    )


                try:

                    place_url = (
                        create_google_maps_place_url(
                            name,
                            place_lat,
                            place_lon
                        )
                    )


                    if place_url:

                        st.link_button(
                            f"🗺️ Open {name} in Google Maps",
                            place_url,
                            key=f"place_map_{index}",
                            use_container_width=True
                        )

                except Exception:

                    pass


                st.divider()


    # ========================================================
    # TRIP BUDGET CALCULATOR
    # ========================================================

    st.divider()

    st.subheader(
        "💰 Trip Budget Calculator"
    )


    b1, b2 = st.columns(2)


    with b1:

        stay_per_day = st.number_input(
            "🏨 Stay per Day ₹",
            min_value=0.0,
            value=1500.0,
            step=100.0
        )


        food_per_person = st.number_input(
            "🍛 Food per Person / Day ₹",
            min_value=0.0,
            value=500.0,
            step=100.0
        )


    with b2:

        activities = st.number_input(
            "🎟️ Activities & Entry Fees ₹",
            min_value=0.0,
            value=500.0,
            step=100.0
        )


        other_expenses = st.number_input(
            "🛍️ Other Expenses ₹",
            min_value=0.0,
            value=300.0,
            step=100.0
        )


    if st.button(
        "💰 Calculate Trip Budget",
        use_container_width=True
    ):

        try:

            result = calculate_trip_budget(

                int(days),

                int(people),

                float(stay_per_day),

                float(food_per_person),

                float(activities),

                float(other_expenses)
            )


            st.session_state.budget_result = (
                result
            )


        except Exception as error:

            st.error(
                f"Budget calculation failed: {error}"
            )


    if st.session_state.budget_result:

        result = (
            st.session_state.budget_result
        )


        st.subheader(
            "📊 Budget Breakdown"
        )


        stay_total = safe_number(
            result.get(
                "stay_total",
                0
            )
        )


        food_total = safe_number(
            result.get(
                "food_total",
                0
            )
        )


        activities_total = safe_number(
            result.get(
                "activities",
                activities
            )
        )


        other_total = safe_number(
            result.get(
                "other_expenses",
                other_expenses
            )
        )


        total = safe_number(
            result.get(
                "total",
                0
            )
        )


        bcol1, bcol2 = st.columns(2)


        with bcol1:

            st.metric(
                "🏨 Stay Total",
                f"₹{stay_total:.2f}"
            )

            st.metric(
                "🍛 Food Total",
                f"₹{food_total:.2f}"
            )


        with bcol2:

            st.metric(
                "🎟️ Activities",
                f"₹{activities_total:.2f}"
            )

            st.metric(
                "🛍️ Other Expenses",
                f"₹{other_total:.2f}"
            )


        st.metric(
            "💰 Total Estimated Expense",
            f"₹{total:.2f}"
        )


        remaining = (
            float(budget) - float(total)
        )


        if remaining >= 0:

            st.success(
                f"🎉 Remaining Budget: ₹{remaining:.2f}"
            )

        else:

            st.warning(
                f"⚠️ Budget Exceeded: ₹{abs(remaining):.2f}"
            )


    # ========================================================
    # CAMERA AI
    # ========================================================

    st.divider()

    st.subheader(
        "📷 Camera AI"
    )


    uploaded_image = st.file_uploader(

        "Upload a tourist place image",

        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )


    if uploaded_image:

        st.image(
            uploaded_image,
            caption="Selected Image",
            use_container_width=True
        )


        if st.button(
            "🔍 Analyze This Place",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Analyzing image..."
                ):

                    prepared_image = (
                        prepare_image_for_vision(
                            uploaded_image
                        )
                    )


                    analysis = (
                        analyze_prepared_image(
                            prepared_image
                        )
                    )


                    st.session_state.camera_analysis = (
                        analysis
                    )


            except Exception as error:

                st.error(
                    f"Camera AI Error: {error}"
                )


    if st.session_state.camera_analysis:

        st.subheader(
            "🧠 Place Analysis"
        )

        st.write(
            st.session_state.camera_analysis
        )


    # ========================================================
    # TOURIST QUESTION
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Ask Tourist AI"
    )


    question = st.text_area(

        "Ask about your trip",

        placeholder=
        "Ooty-la 2 days trip plan pannu..."
    )


    if st.button(
        "✨ Ask Tourist AI",
        use_container_width=True
    ):

        if question.strip():

            try:

                answer = ask_tourist_ai(

                    question,

                    voice="FRIDAY",

                    language="Tamil + English",

                    chat_history=
                        st.session_state
                        .chat_history[-5:]
                )


                st.session_state.chat_history.append(
                    {
                        "user": question,
                        "assistant": answer
                    }
                )


                st.rerun()


            except Exception as error:

                st.error(
                    f"AI Error: {error}"
                )

        else:

            st.warning(
                "Ask something first."
            )


    # ========================================================
    # TOURIST CHAT HISTORY
    # ========================================================

    if st.session_state.chat_history:

        st.divider()

        st.subheader(
            "💬 Tourist AI Chat"
        )


        for chat in (
            st.session_state.chat_history[-6:]
        ):

            with st.chat_message("user"):

                st.markdown(
                    chat["user"]
                )


            with st.chat_message("assistant"):

                st.markdown(
                    chat["assistant"]
                )


    # ========================================================
    # COMPLETE TRIP PLAN
    # ========================================================

    st.divider()

    st.subheader(
        "🗓️ Complete AI Trip Plan"
    )


    if st.button(
        "✨ Create Complete Trip Plan",
        use_container_width=True
    ):

        if not destination.strip():

            st.warning(
                "Please enter destination first."
            )

        else:

            try:

                route_text = ""

                if st.session_state.route:

                    route_text = (
                        f"Route distance: "
                        f"{st.session_state.route.get('distance_km', '')} km. "
                    )


                # SHORT PROMPT
                # Prevents Groq huge request error
                trip_prompt = f"""
Create a practical travel itinerary.

Start: {start_location or "Not specified"}
Destination: {destination}
Days: {int(days)}
People: {int(people)}
Budget: ₹{budget}
Fuel: {fuel_type}
{route_text}

Give:
1. Day-wise plan
2. Important places
3. Suggested travel order
4. Food suggestions
5. Budget tips
6. Travel precautions

Reply in Tamil + English naturally.
Keep the plan useful and not unnecessarily huge.
"""


                with st.spinner(
                    "FRIDAY is creating your trip plan..."
                ):

                    answer = ask_tourist_ai(

                        trip_prompt,

                        voice="FRIDAY",

                        language="Tamil + English",

                        # IMPORTANT:
                        # Empty history prevents 413 huge request
                        chat_history=[]
                    )


                st.session_state.complete_trip_plan = (
                    answer
                )


            except Exception as error:

                st.error(
                    f"Trip Plan Error: {error}"
                )


    if st.session_state.complete_trip_plan:

        st.success(
            "Your Complete Trip Plan is Ready!"
        )

        st.markdown(
            st.session_state.complete_trip_plan
        )
