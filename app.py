import streamlit as st

from src.ai.groq_service import ask_tourist_ai
from src.travel.fuel_calculator import calculate_fuel_cost
from src.maps.distance_service import get_route_distance
from src.budget.budget_calculator import calculate_trip_budget
from src.voice.voice_service import prepare_voice_text

from src.camera.camera_service import (
    prepare_image_for_vision
)

from src.camera.vision_service import (
    analyze_prepared_image
)

from src.maps.map_service import (
    show_interactive_map
)

from src.weather.weather_service import (
    get_weather,
    weather_description
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
# NEW CHAT FUNCTION
# ============================================================

def new_chat():
    """
    Clear current AI/trip session data.
    """

    st.session_state.route = None
    st.session_state.fuel = None
    st.session_state.weather = None
    st.session_state.ai_answer = None
    st.session_state.camera_analysis = None
    st.session_state.voice_data = None
    st.session_state.trip_created = False


# ============================================================
# SESSION STATE
# ============================================================

if "trip_created" not in st.session_state:
    st.session_state.trip_created = False

if "route" not in st.session_state:
    st.session_state.route = None

if "fuel" not in st.session_state:
    st.session_state.fuel = None

if "weather" not in st.session_state:
    st.session_state.weather = None

if "ai_answer" not in st.session_state:
    st.session_state.ai_answer = None

if "camera_analysis" not in st.session_state:
    st.session_state.camera_analysis = None

if "voice_data" not in st.session_state:
    st.session_state.voice_data = None


# ============================================================
# NEW CHAT BUTTON
# ============================================================

top_left, top_right = st.columns([5, 1])

with top_right:

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        new_chat()

        st.rerun()


# ============================================================
# VOICE FUNCTION
# ============================================================

def speak_text(text, voice_name):

    safe_text = (
        text
        .replace("`", "'")
        .replace("\n", " ")
    )

    rate = (
        "0.92"
        if voice_name == "JARVIS"
        else "1.05"
    )

    pitch = (
        "0.85"
        if voice_name == "JARVIS"
        else "1.08"
    )

    html = f"""
    <script>

        const text = {safe_text!r};

        const utterance =
            new SpeechSynthesisUtterance(text);

        utterance.rate = {rate};
        utterance.pitch = {pitch};

        window.speechSynthesis.cancel();

        window.speechSynthesis.speak(
            utterance
        );

    </script>
    """

    st.components.v1.html(
        html,
        height=0
    )


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .stApp {
        background: #0b0f17;
        color: white;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    .title {
        text-align: center;
        padding-top: 20px;
        padding-bottom: 20px;
    }

    .title h1 {
        font-size: 44px;
        margin-bottom: 5px;
    }

    .title p {
        color: #9ca3af;
        font-size: 16px;
    }

    .card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 18px;
    }

    .chat-ai {
        background: #111827;
        border: 1px solid #1f2937;
        padding: 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 10px 0;
    }

    .voice-card {
        text-align: center;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 18px;
    }

    .small-text {
        color: #9ca3af;
        font-size: 14px;
    }

    .stButton > button {
        border-radius: 12px;
        min-height: 45px;
        font-weight: 600;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background: #111827;
        color: white;
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="title">

        <h1>🌍 Tourist AI</h1>

        <p>
            Your intelligent AI travel companion
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AI VOICE
# ============================================================

st.markdown("### 🎙️ Choose Your AI")

voice = st.radio(
    "AI Voice",
    [
        "🦾 JARVIS",
        "🕷️ EDY"
    ],
    horizontal=True,
    label_visibility="collapsed"
)


if voice == "🦾 JARVIS":

    voice_name = "JARVIS"

    voice_description = (
        "Calm • Intelligent • Professional"
    )

else:

    voice_name = "EDY"

    voice_description = (
        "Friendly • Energetic • Casual"
    )


st.markdown(
    f"""
    <div class="voice-card">

        <h3>{voice}</h3>

        <span class="small-text">
            {voice_description}
        </span>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TRIP DETAILS
# ============================================================

st.markdown("### ✈️ Plan Your Trip")

col1, col2 = st.columns(2)


with col1:

    start_location = st.text_input(
        "📍 Starting Location",
        placeholder="Example: Madurai"
    )


with col2:

    destination = st.text_input(
        "🌍 Destination",
        placeholder="Example: Ooty"
    )


col3, col4, col5 = st.columns(3)


with col3:

    days = st.number_input(
        "📅 Number of Days",
        min_value=1,
        max_value=30,
        value=2
    )


with col4:

    people = st.number_input(
        "👥 Number of People",
        min_value=1,
        max_value=50,
        value=2
    )


with col5:

    budget = st.number_input(
        "💰 Total Budget (₹)",
        min_value=0.0,
        value=5000.0,
        step=500.0
    )


# ============================================================
# TRAVEL & FUEL
# ============================================================

st.markdown("### 🚗 Travel & Fuel")

vehicle_col1, vehicle_col2, vehicle_col3 = (
    st.columns(3)
)


with vehicle_col1:

    fuel_type = st.selectbox(
        "⛽ Fuel Type",
        [
            "Petrol",
            "Diesel"
        ]
    )


with vehicle_col2:

    mileage = st.number_input(
        "⚙️ Mileage (km/L)",
        min_value=1.0,
        value=15.0,
        step=0.5
    )


with vehicle_col3:

    fuel_price = st.number_input(
        "💰 Fuel Price (₹/L)",
        min_value=0.0,
        value=100.0,
        step=1.0
    )


# ============================================================
# DISTANCE CALCULATION
# ============================================================

if start_location and destination:

    if st.button(
        "📍 Calculate Distance & Fuel",
        use_container_width=True
    ):

        with st.spinner(
            "Calculating your route... 🗺️"
        ):

            try:

                route = get_route_distance(
                    start_location,
                    destination
                )

                st.session_state.route = route

                fuel = calculate_fuel_cost(
                    distance_km=route["distance_km"],
                    mileage_kmpl=mileage,
                    fuel_price=fuel_price,
                    round_trip=True
                )

                st.session_state.fuel = fuel

                st.success(
                    "Travel calculation completed! 🚗"
                )

            except Exception as error:

                st.error(
                    "Could not calculate the route."
                )

                st.exception(error)


# ============================================================
# ROUTE RESULT
# ============================================================

if st.session_state.route:

    route = st.session_state.route

    distance = route["distance_km"]

    duration = route["duration_minutes"]

    hours = int(duration // 60)

    minutes = int(duration % 60)

    st.markdown("### 🗺️ Route Estimate")

    r1, r2, r3 = st.columns(3)


    with r1:

        st.metric(
            "📍 One-way Distance",
            f"{distance} km"
        )


    with r2:

        st.metric(
            "🔄 Round Trip",
            f"{distance * 2:.1f} km"
        )


    with r3:

        st.metric(
            "⏱️ Driving Time",
            f"{hours}h {minutes}m"
        )


    try:

        show_interactive_map(
            st.session_state.route
        )

    except Exception as error:

        st.warning(
            "Route map could not be displayed."
        )

        st.exception(error)


# ============================================================
# DESTINATION WEATHER
# ============================================================

if st.session_state.route:

    route = st.session_state.route

    latitude = route.get(
        "destination_latitude"
    )

    longitude = route.get(
        "destination_longitude"
    )

    if (
        latitude is not None
        and longitude is not None
    ):

        st.markdown(
            "### 🌦️ Destination Weather"
        )

        if st.button(
            "🌦️ Check Destination Weather",
            use_container_width=True
        ):

            with st.spinner(
                "Getting latest weather... 🌍"
            ):

                try:

                    weather = get_weather(
                        latitude,
                        longitude
                    )

                    st.session_state.weather = (
                        weather
                    )

                except Exception as error:

                    st.error(
                        "Could not get weather."
                    )

                    st.exception(error)


# ============================================================
# WEATHER RESULT
# ============================================================

if st.session_state.weather:

    weather = st.session_state.weather

    description = weather_description(
        weather["weather_code"]
    )

    w1, w2, w3, w4 = st.columns(4)


    with w1:

        st.metric(
            "🌡️ Temperature",
            f"{weather['temperature']} °C"
        )


    with w2:

        st.metric(
            "🤒 Feels Like",
            f"{weather['feels_like']} °C"
        )


    with w3:

        st.metric(
            "💧 Humidity",
            f"{weather['humidity']}%"
        )


    with w4:

        st.metric(
            "💨 Wind",
            f"{weather['wind_speed']} km/h"
        )


    st.info(
        f"**{description}**"
    )


# ============================================================
# FUEL RESULT
# ============================================================

if st.session_state.fuel:

    fuel = st.session_state.fuel

    st.markdown("### ⛽ Fuel Estimate")

    f1, f2, f3 = st.columns(3)


    with f1:

        st.metric(
            "⛽ Fuel Type",
            fuel_type
        )


    with f2:

        st.metric(
            "⛽ Fuel Required",
            f"{fuel['fuel_required_litres']} L"
        )


    with f3:

        st.metric(
            "💰 Estimated Fuel Cost",
            f"₹{fuel['estimated_fuel_cost']:,.0f}"
        )


# ============================================================
# BUDGET DETAILS
# ============================================================

st.markdown("### 💰 Trip Budget")

b1, b2 = st.columns(2)


with b1:

    stay_cost_per_day = st.number_input(
        "🏨 Stay per Day",
        min_value=0.0,
        value=1500.0,
        step=500.0
    )


with b2:

    food_cost_per_day = st.number_input(
        "🍽️ Food per Day",
        min_value=0.0,
        value=1000.0,
        step=500.0
    )


activity_cost = st.number_input(
    "🎟️ Activities / Entry Fees",
    min_value=0.0,
    value=500.0,
    step=100.0
)


other_cost = st.number_input(
    "🛍️ Other Expenses",
    min_value=0.0,
    value=300.0,
    step=100.0
)


# ============================================================
# BUDGET CALCULATION
# ============================================================

if st.session_state.fuel:

    fuel_cost = st.session_state.fuel[
        "estimated_fuel_cost"
    ]

    stay_total = (
        stay_cost_per_day * days
    )

    food_total = (
        food_cost_per_day * days
    )

    try:

        budget_result = calculate_trip_budget(
            total_budget=budget,
            travel_cost=fuel_cost,
            stay_cost=stay_total,
            food_cost=food_total,
            activity_cost=activity_cost,
            other_cost=other_cost
        )

        st.markdown(
            "### 📊 Budget Summary"
        )

        x1, x2, x3 = st.columns(3)


        with x1:

            st.metric(
                "💰 Total Budget",
                f"₹{budget_result['total_budget']:,.0f}"
            )


        with x2:

            st.metric(
                "💸 Estimated Cost",
                f"₹{budget_result['total_cost']:,.0f}"
            )


        with x3:

            st.metric(
                "💵 Remaining",
                f"₹{budget_result['remaining_budget']:,.0f}"
            )


        st.markdown(
            "#### Breakdown"
        )


        st.write(
            f"🚗 Travel: "
            f"₹{budget_result['travel_cost']:,.0f}"
        )


        st.write(
            f"🏨 Stay: "
            f"₹{budget_result['stay_cost']:,.0f}"
        )


        st.write(
            f"🍽️ Food: "
            f"₹{budget_result['food_cost']:,.0f}"
        )


        st.write(
            f"🎟️ Activities: "
            f"₹{budget_result['activity_cost']:,.0f}"
        )


        st.write(
            f"🛍️ Other: "
            f"₹{budget_result['other_cost']:,.0f}"
        )


        if budget_result["within_budget"]:

            st.success(
                "✅ Great! Your estimated trip "
                "is within your budget."
            )

        else:

            st.warning(
                f"⚠️ Your trip is "
                f"₹{abs(budget_result['remaining_budget']):,.0f} "
                f"over the selected budget."
            )


    except Exception as error:

        st.error(
            "Could not calculate the trip budget."
        )

        st.exception(error)


# ============================================================
# CAMERA AI
# ============================================================

st.markdown("---")

st.markdown(
    "### 📷 Tourist Camera AI"
)

camera_image = st.camera_input(
    "📷 Take a photo of the place"
)


uploaded_image = st.file_uploader(
    "🖼️ Or upload a travel image",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


selected_image = (
    camera_image
    if camera_image is not None
    else uploaded_image
)


if selected_image is not None:

    image_result = prepare_image_for_vision(
        selected_image
    )


    if image_result["success"]:

        st.image(
            image_result["image"],
            caption="📍 Travel Image",
            use_container_width=True
        )


        st.caption(
            f"Image: "
            f"{image_result['width']} × "
            f"{image_result['height']} px"
        )


        if st.button(
            "🔎 Analyze This Place",
            use_container_width=True
        ):

            with st.spinner(
                f"{voice_name} is analyzing "
                "the image... 👁️"
            ):

                try:

                    analysis = (
                        analyze_prepared_image(
                            image_result,
                            voice=voice_name,
                            language="Tamil + English"
                        )
                    )

                    st.session_state.camera_analysis = (
                        analysis
                    )


                except Exception as error:

                    st.error(
                        "❌ Could not analyze the image."
                    )

                    st.exception(error)


    else:

        st.error(
            image_result["message"]
        )


# ============================================================
# CAMERA AI RESULT
# ============================================================

if st.session_state.camera_analysis:

    st.markdown(
        "### 📍 Place Analysis"
    )


    st.markdown(
        f"""
        <div class="chat-ai">

            <b>{voice}</b>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        st.session_state.camera_analysis
    )


    if st.button(
        "🔊 Speak Place Analysis",
        key="speak_camera_analysis"
    ):

        speak_text(
            st.session_state.camera_analysis,
            voice_name
        )


# ============================================================
# AI TRIP PLANNER
# ============================================================

st.markdown("---")

st.markdown(
    "### 🧠 Ask Tourist AI"
)


user_question = st.text_area(
    "Ask anything about your trip",
    placeholder=(
        "Example: ₹5000 budget-la Ooty 2 days "
        "trip plan pannu..."
    ),
    height=100
)


# ============================================================
# WEATHER CONTEXT FOR AI
# ============================================================

weather_context = ""


if st.session_state.weather:

    weather = st.session_state.weather

    weather_context = f"""
Current destination weather:

Temperature:
{weather['temperature']} °C

Feels like:
{weather['feels_like']} °C

Humidity:
{weather['humidity']}%

Wind:
{weather['wind_speed']} km/h

Condition:
{weather_description(weather['weather_code'])}

Use this weather information when the
user asks about current destination weather.
"""


# ============================================================
# ASK AI
# ============================================================

if st.button(
    f"✨ Ask {voice_name}",
    use_container_width=True
):

    if not user_question.strip():

        st.warning(
            "Please enter your travel question."
        )

    else:

        with st.spinner(
            f"{voice_name} is thinking... 🤖"
        ):

            try:

                complete_question = (
                    user_question
                    + "\n\n"
                    + weather_context
                )


                answer = ask_tourist_ai(
                    complete_question,
                    voice=voice_name,
                    language="Tamil + English"
                )


                st.session_state.ai_answer = (
                    answer
                )


            except Exception as error:

                st.error(
                    "❌ Tourist AI Error"
                )

                st.exception(error)


# ============================================================
# AI RESPONSE
# ============================================================

if st.session_state.ai_answer:

    st.markdown(
        "### 💬 Tourist AI"
    )


    st.markdown(
        f"""
        <div class="chat-ai">

            <b>{voice}</b>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        st.session_state.ai_answer
    )


    if st.button(
        "🔊 Speak Response",
        key="speak_ai_response"
    ):

        speak_text(
            st.session_state.ai_answer,
            voice_name
        )


# ============================================================
# CREATE COMPLETE TRIP
# ============================================================

st.markdown("---")

if st.button(
    "🚀 Create Complete Trip Plan",
    use_container_width=True
):

    if (
        not start_location
        or not destination
    ):

        st.warning(
            "Please enter starting location "
            "and destination first."
        )

    else:

        with st.spinner(
            f"{voice_name} is creating "
            "your complete trip... 🤖"
        ):

            try:

                # ------------------------------------------------
                # ROUTE TEXT
                # ------------------------------------------------

                route_text = (
                    "Distance not calculated yet."
                )


                if st.session_state.route:

                    route = st.session_state.route

                    route_text = (
                        f"{route['distance_km']} km "
                        f"one-way, "
                        f"{route['duration_minutes']} "
                        f"minutes"
                    )


                # ------------------------------------------------
                # FUEL TEXT
                # ------------------------------------------------

                fuel_text = (
                    "Fuel estimate not calculated yet."
                )


                if st.session_state.fuel:

                    fuel = st.session_state.fuel

                    fuel_text = (
                        f"{fuel['fuel_required_litres']} L, "
                        f"₹{fuel['estimated_fuel_cost']}"
                    )


                # ------------------------------------------------
                # WEATHER TEXT
                # ------------------------------------------------

                weather_text = (
                    "Weather not checked yet."
                )


                if st.session_state.weather:

                    weather = st.session_state.weather

                    weather_text = (
                        f"{weather['temperature']} °C, "
                        f"{weather_description(weather['weather_code'])}, "
                        f"humidity "
                        f"{weather['humidity']}%"
                    )


                # ------------------------------------------------
                # COMPLETE PROMPT
                # ------------------------------------------------

                prompt = f"""
Create a complete tourist trip plan.

Starting location:
{start_location}

Destination:
{destination}

Number of days:
{days}

Number of people:
{people}

Total budget:
₹{budget}

Fuel type:
{fuel_type}

Vehicle mileage:
{mileage} km/L

Route:
{route_text}

Fuel estimate:
{fuel_text}

Destination weather:
{weather_text}

Stay per day:
₹{stay_cost_per_day}

Food per day:
₹{food_cost_per_day}

Activities:
₹{activity_cost}

Other expenses:
₹{other_cost}

Create:

1. Day-by-day itinerary
2. Best tourist places
3. Travel order
4. Estimated travel cost
5. Fuel estimate
6. Stay estimate
7. Food estimate
8. Activities estimate
9. Total budget
10. Money remaining
11. Useful travel tips

Use Tamil + English naturally.

Do not claim live information unless it
is actually provided by a connected
live service.

Clearly identify estimates.
"""


                # ------------------------------------------------
                # ASK AI
                # ------------------------------------------------

                answer = ask_tourist_ai(
                    prompt,
                    voice=voice_name,
                    language="Tamil + English"
                )


                # ------------------------------------------------
                # VOICE PREPARATION
                # ------------------------------------------------

                voice_data = prepare_voice_text(
                    answer,
                    voice_name
                )


                st.session_state.voice_data = (
                    voice_data
                )

                st.session_state.ai_answer = (
                    answer
                )

                st.session_state.trip_created = (
                    True
                )


                st.success(
                    f"{voice_name} completed "
                    "your trip plan! 🚀"
                )


                st.markdown(
                    "### 🧳 Your Complete Trip"
                )


                st.markdown(
                    answer
                )


            except Exception as error:

                st.error(
                    "Could not create the "
                    "complete trip plan."
                )

                st.exception(error)


# ============================================================
# FEATURES
# ============================================================

st.markdown("---")

st.markdown(
    "### 🚀 Tourist AI Features"
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.markdown(
        """
        <div class="card">

            📍<br>

            <b>Smart Routes</b><br>

            Distance and travel-time
            estimation.

        </div>
        """,
        unsafe_allow_html=True
    )


with c2:

    st.markdown(
        """
        <div class="card">

            💰<br>

            <b>Budget AI</b><br>

            Build trips around
            your budget.

        </div>
        """,
        unsafe_allow_html=True
    )


with c3:

    st.markdown(
        """
        <div class="card">

            📷<br>

            <b>Camera AI</b><br>

            Analyze tourist-place
            photos.

        </div>
        """,
        unsafe_allow_html=True
    )


with c4:

    st.markdown(
        """
        <div class="card">

            🎙️<br>

            <b>JARVIS + EDY</b><br>

            Your two AI travel
            personalities.

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#6b7280;
        padding:20px;
    ">

        🌍 Tourist AI

        <br>

        Your intelligent travel companion

    </div>
    """,
    unsafe_allow_html=True
)
