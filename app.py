app.py

import streamlit as st
import textwrap

from src.ai.groq_service import ask_tourist_ai
from src.travel.fuel_calculator import calculate_fuel_cost
from src.maps.distance_service import get_route_distance
from src.maps.map_service import show_interactive_map
from src.maps.nearby_service import (
    get_nearby_places,
    create_google_maps_place_url
)
from src.budget.budget_calculator import calculate_trip_budget
from src.camera.camera_service import prepare_image_for_vision
from src.camera.vision_service import analyze_prepared_image
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
    "chat_history": [],
    "route": None,
    "fuel": None,
    "weather": None,
    "camera_analysis": None,
    "nearby_places": [],
    "budget_result": None
}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# NEW CHAT
# ============================================================

def new_chat():

    st.session_state.chat_history = []
    st.session_state.camera_analysis = None

    st.rerun()


# ============================================================
# SPEAK FUNCTION
# ============================================================

def speak_text(text, voice_name):

    safe_text = (
        str(text)
        .replace("`", "'")
        .replace("\n", " ")
    )

    if voice_name == "JARVIS":

        rate = 0.92
        pitch = 0.85

    else:

        rate = 1.05
        pitch = 1.08

    html = f"""
    <script>

    const text = {safe_text!r};

    const utterance =
        new SpeechSynthesisUtterance(text);

    const voices =
        window.speechSynthesis.getVoices();

    let selectedVoice = null;

    if ("{voice_name}" === "JARVIS") {{

        selectedVoice = voices.find(
            voice =>
            /male|david|mark|daniel|alex/i
            .test(voice.name)
        );

    }} else {{

        selectedVoice = voices.find(
            voice =>
            /female|samantha|zira|karen/i
            .test(voice.name)
        );

    }}

    if (selectedVoice) {{

        utterance.voice = selectedVoice;

    }}

    utterance.rate = {rate};
    utterance.pitch = {pitch};
    utterance.volume = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);

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
        max-width: 1200px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    .title {
        text-align: center;
        padding: 15px;
    }

    .title h1 {
        font-size: 46px;
        margin-bottom: 5px;
    }

    .title p {
        color: #9ca3af;
    }

    .card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 15px;
    }

    .chat-ai {
        background: #111827;
        border: 1px solid #263244;
        padding: 18px;
        border-radius: 18px 18px 18px 4px;
        margin-top: 10px;
    }

    .chat-user {
        background: #172033;
        border: 1px solid #273449;
        padding: 18px;
        border-radius: 18px 18px 4px 18px;
        margin-top: 10px;
    }

    .feature-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 20px;
        min-height: 145px;
        margin-bottom: 15px;
    }

    .feature-icon {
        font-size: 30px;
    }

    .feature-title {
        font-size: 18px;
        font-weight: 700;
        margin-top: 8px;
    }

    .feature-text {
        color: #9ca3af;
        font-size: 14px;
        margin-top: 7px;
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
# NEW CHAT
# ============================================================

top1, top2, top3 = st.columns([1, 2, 1])

with top2:

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        new_chat()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="title">
        <h1>🌍 Tourist AI</h1>
        <p>Plan • Explore • Discover • Travel Smarter</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# VOICE SELECTION
# ============================================================

st.markdown("### 🎙️ Choose Your AI")

voice = st.radio(
    "Voice",
    ["🦾 JARVIS", "🕷️ EDY"],
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


st.info(
    f"🤖 **{voice_name}** — {voice_description}"
)


# ============================================================
# AI MODE
# ============================================================

st.markdown("### 🧠 AI Mode")

ai_mode = st.selectbox(
    "Choose AI Mode",
    [
        "🤖 Normal AI",
        "🧠 Smart Trip Planner",
        "📍 Travel Expert",
        "⚡ Quick Mode"
    ]
)


mode_name = ai_mode.split(
    " ", 1
)[1]


# ============================================================
# TRIP DETAILS
# ============================================================

st.markdown("---")
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
        "💰 Total Budget ₹",
        min_value=0.0,
        value=5000.0,
        step=500.0
    )


# ============================================================
# TRAVEL + FUEL
# ============================================================

st.markdown("### 🚗 Travel & Fuel")

f1, f2, f3 = st.columns(3)

with f1:

    fuel_type = st.selectbox(
        "⛽ Fuel Type",
        ["Petrol", "Diesel"]
    )

with f2:

    mileage = st.number_input(
        "⚙️ Mileage km/L",
        min_value=1.0,
        value=15.0,
        step=0.5
    )

with f3:

    fuel_price = st.number_input(
        "💰 Fuel Price ₹/L",
        min_value=0.0,
        value=100.0,
        step=1.0
    )


# ============================================================
# ROUTE CALCULATION
# ============================================================

if start_location and destination:

    if st.button(
        "📍 Calculate Route & Fuel",
        use_container_width=True
    ):

        with st.spinner(
            "Calculating route... 🗺️"
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
                    "Route calculated successfully! 🚗"
                )

            except Exception as error:

                st.error(
                    f"Route calculation failed: {error}"
                )


# ============================================================
# ROUTE RESULT
# ============================================================

if st.session_state.route:

    route = st.session_state.route

    distance = route["distance_km"]
    duration = route["duration_minutes"]

    hours = duration // 60
    minutes = duration % 60

    st.markdown("### 🗺️ Route Result")

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

        show_interactive_map(route)

    except Exception:

        st.warning(
            "Interactive map could not be displayed."
        )


# ============================================================
# WEATHER
# ============================================================

if st.session_state.route:

    route = st.session_state.route

    latitude = route.get(
        "destination_latitude"
    )

    longitude = route.get(
        "destination_longitude"
    )

    st.markdown("### 🌦️ Destination Weather")

    if st.button(
        "🌦️ Check Live Weather",
        use_container_width=True
    ):

        try:

            with st.spinner(
                "Getting weather..."
            ):

                st.session_state.weather = get_weather(
                    latitude,
                    longitude
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

    description = weather_description(
        weather["weather_code"]
    )

    st.info(
        f"{description}\n\n"
        f"{get_weather_advice(weather)}"
    )


# ============================================================
# FUEL RESULT
# ============================================================

if st.session_state.fuel:

    fuel = st.session_state.fuel

    st.markdown("### ⛽ Fuel Estimate")

    fuel1, fuel2, fuel3 = st.columns(3)

    with fuel1:

        st.metric(
            "Fuel Type",
            fuel_type
        )

    with fuel2:

        st.metric(
            "Fuel Required",
            f"{fuel['fuel_required_litres']} L"
        )

    with fuel3:

        st.metric(
            "Estimated Cost",
            f"₹{fuel['estimated_fuel_cost']:,.0f}"
        )


# ============================================================
# NEARBY PLACES
# ============================================================

if st.session_state.route:

    st.markdown("---")
    st.markdown("### 📍 Discover Nearby Places")

    place_type = st.selectbox(
        "Find Nearby",
        [
            "restaurant",
            "hotel",
            "cafe",
            "food"
        ]
    )

    radius_km = st.selectbox(
        "Search Radius",
        [2, 5, 10, 15],
        index=1
    )

    if st.button(
        "🔍 Find Nearby Places",
        use_container_width=True
    ):

        try:

            with st.spinner(
                "Searching real nearby places... 📍"
            ):

                route = st.session_state.route

                places = get_nearby_places(
                    route["destination_latitude"],
                    route["destination_longitude"],
                    place_type=place_type,
                    radius=radius_km * 1000
                )

                st.session_state.nearby_places = places

        except Exception as error:

            st.error(
                f"Nearby search failed: {error}"
            )


if st.session_state.nearby_places:

    for place in st.session_state.nearby_places:

        with st.container():

            st.markdown(
                f"""
                <div class="card">
                    <h4>📍 {place['name']}</h4>
                    <p>
                        📏 {place['distance_km']} km away
                        <br>
                        🏷️ {place['category']}
                        <br>
                        📌 {place['address']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            maps_url = create_google_maps_place_url(
                place["latitude"],
                place["longitude"]
            )

            st.link_button(
                "🗺️ Open in Maps",
                maps_url,
                use_container_width=True
            )


# ============================================================
# BUDGET
# ============================================================

st.markdown("---")
st.markdown("### 💰 Trip Budget")

b1, b2 = st.columns(2)

with b1:

    stay_cost_per_day = st.number_input(
        "🏨 Stay per Day ₹",
        min_value=0.0,
        value=1500.0,
        step=500.0
    )

with b2:

    food_cost_per_day = st.number_input(
        "🍽️ Food per Day ₹",
        min_value=0.0,
        value=1000.0,
        step=500.0
    )


activity_cost = st.number_input(
    "🎟️ Activities / Entry Fees ₹",
    min_value=0.0,
    value=500.0,
    step=100.0
)

other_cost = st.number_input(
    "🛍️ Other Expenses ₹",
    min_value=0.0,
    value=300.0,
    step=100.0
)


if st.session_state.fuel:

    fuel_cost = (
        st.session_state.fuel[
            "estimated_fuel_cost"
        ]
    )

    budget_result = calculate_trip_budget(
        total_budget=budget,
        travel_cost=fuel_cost,
        stay_cost=stay_cost_per_day * days,
        food_cost=food_cost_per_day * days,
        activity_cost=activity_cost,
        other_cost=other_cost
    )

    st.session_state.budget_result = (
        budget_result
    )

    st.markdown("### 📊 Budget Summary")

    x1, x2, x3 = st.columns(3)

    with x1:

        st.metric(
            "Total Budget",
            f"₹{budget_result['total_budget']:,.0f}"
        )

    with x2:

        st.metric(
            "Estimated Cost",
            f"₹{budget_result['total_cost']:,.0f}"
        )

    with x3:

        st.metric(
            "Remaining",
            f"₹{budget_result['remaining_budget']:,.0f}"
        )

    if budget_result["within_budget"]:

        st.success(
            "✅ Your trip is within budget!"
        )

    else:

        st.warning(
            "⚠️ Estimated trip cost exceeds your budget."
        )


# ============================================================
# CAMERA AI
# ============================================================

st.markdown("---")
st.markdown("### 📷 Tourist Camera AI")

camera_image = st.camera_input(
    "Take a photo"
)

uploaded_image = st.file_uploader(
    "Or upload a travel image",
    type=["jpg", "jpeg", "png", "webp"]
)

selected_image = (
    camera_image
    if camera_image is not None
    else uploaded_image
)


if selected_image:

    image_result = prepare_image_for_vision(
        selected_image
    )

    if image_result["success"]:

        st.image(
            image_result["image"],
            use_container_width=True
        )

        if st.button(
            "🔎 Analyze This Place",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    f"{voice_name} is analyzing..."
                ):

                    analysis = analyze_prepared_image(
                        image_result,
                        voice=voice_name,
                        language="Tamil + English"
                    )

                    st.session_state.camera_analysis = (
                        analysis
                    )

            except Exception as error:

                st.error(
                    f"Camera AI failed: {error}"
                )


if st.session_state.camera_analysis:

    st.markdown("### 📍 Place Analysis")

    st.markdown(
        st.session_state.camera_analysis
    )

    if st.button(
        "🔊 Speak Place Analysis"
    ):

        speak_text(
            st.session_state.camera_analysis,
            voice_name
        )


# ============================================================
# BUILD AI CONTEXT
# ============================================================

def build_ai_context():

    context = f"""

AI Mode:
{mode_name}

Starting Location:
{start_location or "Not provided"}

Destination:
{destination or "Not provided"}

Days:
{days}

People:
{people}

Budget:
₹{budget}

Fuel:
{fuel_type}

Mileage:
{mileage} km/L
"""

    if st.session_state.route:

        route = st.session_state.route

        context += f"""

Route:
Distance: {route['distance_km']} km
Driving time: {route['duration_minutes']} minutes
"""

    if st.session_state.fuel:

        fuel = st.session_state.fuel

        context += f"""

Fuel Estimate:
Fuel required: {fuel['fuel_required_litres']} L
Fuel cost: ₹{fuel['estimated_fuel_cost']}
"""

    if st.session_state.weather:

        weather = st.session_state.weather

        context += f"""

Latest Weather:
Temperature: {weather['temperature']} °C
Humidity: {weather['humidity']}%
Condition:
{weather_description(weather['weather_code'])}
"""

    return context


# ============================================================
# ASK TOURIST AI
# ============================================================

st.markdown("---")
st.markdown("### 🧠 Ask Tourist AI")

user_question = st.text_area(
    "Ask anything about your trip",
    placeholder=(
        "Example: Ooty-la 2 days "
        "budget trip plan pannu..."
    ),
    height=110
)


if st.button(
    f"✨ Ask {voice_name}",
    use_container_width=True
):

    if not user_question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        try:

            with st.spinner(
                f"{voice_name} is thinking..."
            ):

                context = build_ai_context()

                mode_instruction = {

                    "Normal AI":
                    "Answer naturally and helpfully.",

                    "Smart Trip Planner":
                    (
                        "Create detailed practical trip "
                        "plans using available route, "
                        "budget, fuel and weather data."
                    ),

                    "Travel Expert":
                    (
                        "Focus on tourist places, "
                        "culture, attractions, food "
                        "and travel tips."
                    ),

                    "Quick Mode":
                    (
                        "Give a short, direct and useful "
                        "answer."
                    )

                }.get(
                    mode_name,
                    "Answer helpfully."
                )

                final_question = f"""
{context}

Mode instruction:
{mode_instruction}

User Question:
{user_question}

Answer in natural Tamil + English.

Use available trip data when useful.

Do not invent live prices,
weather or availability.
"""

                answer = ask_tourist_ai(
                    final_question,
                    voice=voice_name,
                    language="Tamil + English",
                    chat_history=
                    st.session_state.chat_history
                )

                st.session_state.chat_history.append(
                    {
                        "user": user_question,
                        "assistant": answer,
                        "voice": voice_name
                    }
                )

                st.rerun()

        except Exception as error:

            st.error(
                f"❌ Tourist AI Error: {error}"
            )


# ============================================================
# CHAT HISTORY
# ============================================================

if st.session_state.chat_history:

    st.markdown("---")
    st.markdown("### 💬 Tourist AI Chat")

    for index, chat in enumerate(
        st.session_state.chat_history
    ):

        st.markdown(
            f"""
            <div class="chat-user">
                <b>👤 You</b>
                <br><br>
                {chat['user']}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="chat-ai">
                <b>🤖 {chat['voice']}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            chat["assistant"]
        )

        if st.button(
            "🔊 Speak Response",
            key=f"speak_{index}"
        ):

            speak_text(
                chat["assistant"],
                chat["voice"]
            )


# ============================================================
# COMPLETE TRIP PLAN
# ============================================================

st.markdown("---")

if st.button(
    "🚀 Create Complete Trip Plan",
    use_container_width=True
):

    if not start_location or not destination:

        st.warning(
            "Enter starting location "
            "and destination first."
        )

    else:

        try:

            with st.spinner(
                f"{voice_name} is creating "
                "your complete trip..."
            ):

                context = build_ai_context()

                prompt = f"""
{context}

Create a complete practical tourist trip plan.

Include:

1. 🗺️ Route summary
2. 🌦️ Weather advice
3. 📅 Day-by-day itinerary
4. 📍 Important places to visit
5. 🍽️ Food suggestions
6. 🏨 Stay suggestions
7. 💰 Budget planning
8. 🚗 Fuel and travel tips
9. 🎒 Things to carry
10. ⚠️ Important travel notes

AI Mode:
Smart Trip Planner

Make the plan practical.

Respond naturally in Tamil + English.
"""

                answer = ask_tourist_ai(
                    prompt,
                    voice=voice_name,
                    language="Tamil + English",
                    chat_history=
                    st.session_state.chat_history
                )

                st.session_state.chat_history.append(
                    {
                        "user":
                        "🚀 Create Complete Trip Plan",
                        "assistant": answer,
                        "voice": voice_name
                    }
                )

                st.success(
                    "🎉 Complete trip plan created!"
                )

                st.rerun()

        except Exception as error:

            st.error(
                f"Could not create trip plan: {error}"
            )

