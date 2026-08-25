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
    "general_chat_history": [],
    "route": None,
    "fuel": None,
    "weather": None,
    "camera_analysis": None,
    "nearby_places": [],
    "budget_result": None,
    "app_mode": "🌍 Tourist AI"
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

    st.session_state.route = None
    st.session_state.fuel = None
    st.session_state.weather = None

    st.session_state.camera_analysis = None
    st.session_state.nearby_places = []
    st.session_state.budget_result = None

    st.rerun()


# ============================================================
# CLEAR GENERAL CHAT
# ============================================================

def clear_general_chat():

    st.session_state.general_chat_history = []

    st.rerun()


# ============================================================
# SPEAK FUNCTION
# ============================================================

def speak_text(text, voice_name):

    safe_text = (
        str(text)
        .replace("`", "'")
        .replace("\n", " ")
        .replace("\\", "\\\\")
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

    function speakNow() {{

        if (!window.speechSynthesis) {{
            return;
        }}

        window.speechSynthesis.cancel();

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
                /female|samantha|zira|karen|zira/i
                .test(voice.name)
            );

        }}

        if (!selectedVoice) {{

            selectedVoice = voices.find(
                voice =>
                /en-IN|en-US|en-GB/i
                .test(voice.lang)
            );

        }}

        if (selectedVoice) {{

            utterance.voice = selectedVoice;

        }}

        utterance.rate = {rate};
        utterance.pitch = {pitch};
        utterance.volume = 1;

        window.speechSynthesis.speak(
            utterance
        );

    }}

    if (
        window.speechSynthesis.getVoices().length === 0
    ) {{

        window.speechSynthesis.addEventListener(
            "voiceschanged",
            speakNow,
            {{ once: true }}
        );

    }} else {{

        speakNow();

    }}

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
    textwrap.dedent(
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
            padding: 20px 15px;
        }

        .title h1 {
            font-size: 46px;
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
            padding: 20px;
            margin-bottom: 15px;
        }

        .chat-ai {
            background: #111827;
            border: 1px solid #263244;
            padding: 18px;
            border-radius: 18px 18px 18px 4px;
            margin-top: 12px;
            margin-bottom: 8px;
        }

        .chat-user {
            background: #172033;
            border: 1px solid #273449;
            padding: 18px;
            border-radius: 18px 18px 4px 18px;
            margin-top: 12px;
            margin-bottom: 8px;
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

        .chat-header {
            text-align: center;
            padding: 30px 10px;
        }

        .chat-header h1 {
            font-size: 40px;
            margin-bottom: 8px;
        }

        .chat-header p {
            color: #9ca3af;
        }

        .welcome-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            text-align: center;
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

        div[data-testid="stChatMessage"] {
            border-radius: 15px;
        }

        </style>
        """
    ),
    unsafe_allow_html=True
)


# ============================================================
# TOP NAVIGATION
# ============================================================

nav1, nav2, nav3 = st.columns(
    [1, 1, 1]
)

with nav1:

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        new_chat()


with nav2:

    if st.button(
        "🌍 Tourist AI",
        use_container_width=True
    ):

        st.session_state.app_mode = "🌍 Tourist AI"
        st.rerun()


with nav3:

    if st.button(
        "💬 Chat Mode",
        use_container_width=True
    ):

        st.session_state.app_mode = "💬 Chat Mode"
        st.rerun()


# ============================================================
# SHARED VOICE SELECTION
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


# ============================================================
# GENERAL CHAT MODE
# ============================================================

if st.session_state.app_mode == "💬 Chat Mode":

    st.markdown(
        """
        <div class="chat-header">
            <h1>💬 AI Chat</h1>
            <p>
                Ask anything • Tamil + English • General AI
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    top_left, top_right = st.columns(2)

    with top_left:

        st.info(
            f"🤖 **{voice_name}** — "
            f"{voice_description}"
        )

    with top_right:

        if st.button(
            "🗑️ Clear Chat",
            use_container_width=True
        ):

            clear_general_chat()


    # ========================================================
    # WELCOME SCREEN
    # ========================================================

    if not st.session_state.general_chat_history:

        st.markdown(
            """
            <div class="welcome-card">
                <h2>👋 Hello!</h2>
                <p>
                    I can help with studies, coding,
                    ideas, technology, writing,
                    general questions and more.
                </p>
                <p>
                    Tamil, English or Tanglish —
                    ask naturally! 🚀
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # DISPLAY CHAT HISTORY
    # ========================================================

    for index, message in enumerate(
        st.session_state.general_chat_history
    ):

        if message["role"] == "user":

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    message["content"]
                )

        else:

            with st.chat_message(
                "assistant"
            ):

                st.markdown(
                    message["content"]
                )

                speak_col1, speak_col2 = (
                    st.columns([1, 4])
                )

                with speak_col1:

                    if st.button(
                        "🔊 Speak",
                        key=f"general_speak_{index}"
                    ):

                        speak_text(
                            message["content"],
                            message.get(
                                "voice",
                                voice_name
                            )
                        )


    # ========================================================
    # VOICE INPUT
    # ========================================================

    st.markdown("---")
    st.markdown("### 🎤 Voice Input")

    general_audio = st.audio_input(
        "Tap microphone and record your question",
        key="general_voice_input"
    )

    if general_audio is not None:

        st.audio(
            general_audio
        )

        st.info(
            "🎤 Voice recorded successfully. "
            "Speech-to-text can be connected next "
            "using Groq Whisper transcription."
        )


    # ========================================================
    # CHAT INPUT
    # ========================================================

    user_prompt = st.chat_input(
        "Message AI..."
    )

    if user_prompt:

        st.session_state.general_chat_history.append(
            {
                "role": "user",
                "content": user_prompt
            }
        )

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                f"{voice_name} is thinking..."
            ):

                try:

                    chat_context = ""

                    for message in (
                        st.session_state
                        .general_chat_history[-10:]
                    ):

                        role = message["role"]

                        content = (
                            message["content"]
                        )

                        chat_context += (
                            f"{role}: {content}\n"
                        )


                    prompt = f"""
You are a general-purpose AI assistant.

Your personality is:
{voice_name}

Voice personality:
{voice_description}

You are not limited to tourism.

You can help with:
- General questions
- Education
- Computer Science
- Programming
- Technology
- Ideas
- Writing
- Travel
- Daily questions

Conversation history:

{chat_context}

Respond naturally in Tamil, English
or Tanglish depending on the user's language.

Be friendly, clear and useful.
"""

                    answer = ask_tourist_ai(
                        prompt,
                        voice=voice_name,
                        language="Tamil + English"
                    )

                    st.markdown(
                        answer
                    )

                    st.session_state.general_chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "voice": voice_name
                        }
                    )

                except Exception as error:

                    st.error(
                        f"AI Error: {error}"
                    )

    st.stop()


# ============================================================
# TOURIST AI HEADER
# ============================================================

st.markdown(
    """
    <div class="title">
        <h1>🌍 Tourist AI</h1>
        <p>
            Plan • Explore • Discover • Travel Smarter
        </p>
    </div>
    """,
    unsafe_allow_html=True
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


mode_map = {
    "🤖 Normal AI": "Normal AI",
    "🧠 Smart Trip Planner": "Smart Trip Planner",
    "📍 Travel Expert": "Travel Expert",
    "⚡ Quick Mode": "Quick Mode"
}

mode_name = mode_map.get(
    ai_mode,
    "Normal AI"
)


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

fuel_col1, fuel_col2, fuel_col3 = st.columns(3)

with fuel_col1:

    fuel_type = st.selectbox(
        "⛽ Fuel Type",
        ["Petrol", "Diesel"]
    )

with fuel_col2:

    mileage = st.number_input(
        "⚙️ Mileage km/L",
        min_value=1.0,
        value=15.0,
        step=0.5
    )

with fuel_col3:

    fuel_price = st.number_input(
        "💰 Fuel Price ₹/L",
        min_value=0.0,
        value=100.0,
        step=1.0
    )


# ============================================================
# ROUTE CALCULATION
# ============================================================

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
                    distance_km=float(
                        route["distance_km"]
                    ),
                    mileage_kmpl=float(
                        mileage
                    ),
                    fuel_price=float(
                        fuel_price
                    ),
                    round_trip=True
                )

                st.session_state.fuel = fuel
                st.session_state.weather = None
                st.session_state.nearby_places = []

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

    distance = float(
        route.get(
            "distance_km",
            0
        )
    )

    duration = float(
        route.get(
            "duration_minutes",
            0
        )
    )

    hours = int(
        duration // 60
    )

    minutes = int(
        duration % 60
    )

    st.markdown("### 🗺️ Route Result")

    route_col1, route_col2, route_col3 = (
        st.columns(3)
    )

    with route_col1:

        st.metric(
            "📍 One-way Distance",
            f"{distance:.1f} km"
        )

    with route_col2:

        st.metric(
            "🔄 Round Trip",
            f"{distance * 2:.1f} km"
        )

    with route_col3:

        st.metric(
            "⏱️ Driving Time",
            f"{hours}h {minutes}m"
        )

    try:

        show_interactive_map(
            route
        )

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

    if (
        latitude is None
        or longitude is None
    ):

        st.warning(
            "Destination coordinates are unavailable."
        )

    else:

        if st.button(
            "🌦️ Check Live Weather",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Getting latest weather... 🌦️"
                ):

                    weather = get_weather(
                        latitude,
                        longitude
                    )

                    st.session_state.weather = (
                        weather
                    )

                st.success(
                    "Weather loaded successfully!"
                )

            except Exception as error:

                st.error(
                    f"Weather unavailable: {error}"
                )


# ============================================================
# WEATHER RESULT
# ============================================================

if st.session_state.weather:

    weather = (
        st.session_state.weather
    )

    weather_col1, weather_col2, weather_col3, weather_col4 = (
        st.columns(4)
    )

    with weather_col1:

        st.metric(
            "🌡️ Temperature",
            f"{weather['temperature']} °C"
        )

    with weather_col2:

        st.metric(
            "🤒 Feels Like",
            f"{weather['feels_like']} °C"
        )

    with weather_col3:

        st.metric(
            "💧 Humidity",
            f"{weather['humidity']}%"
        )

    with weather_col4:

        st.metric(
            "💨 Wind",
            f"{weather['wind_speed']} km/h"
        )

    description = weather_description(
        weather["weather_code"]
    )

    advice = get_weather_advice(
        weather
    )

    st.info(
        f"**{description}**\n\n{advice}"
    )


# ============================================================
# FUEL RESULT
# ============================================================

if st.session_state.fuel:

    fuel = st.session_state.fuel

    st.markdown("### ⛽ Fuel Estimate")

    fuel_result1, fuel_result2, fuel_result3 = (
        st.columns(3)
    )

    with fuel_result1:

        st.metric(
            "Fuel Type",
            fuel_type
        )

    with fuel_result2:

        st.metric(
            "Fuel Required",
            f"{fuel['fuel_required_litres']} L"
        )

    with fuel_result3:

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

    nearby_col1, nearby_col2 = (
        st.columns(2)
    )

    with nearby_col1:

        place_type = st.selectbox(
            "Find Nearby",
            [
                "restaurant",
                "hotel",
                "cafe",
                "food"
            ]
        )

    with nearby_col2:

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

            route = st.session_state.route

            latitude = route.get(
                "destination_latitude"
            )

            longitude = route.get(
                "destination_longitude"
            )

            if (
                latitude is None
                or longitude is None
            ):

                st.warning(
                    "Destination coordinates unavailable."
                )

            else:

                with st.spinner(
                    "Searching nearby places... 📍"
                ):

                    places = get_nearby_places(
                        latitude,
                        longitude,
                        place_type=place_type,
                        radius=radius_km * 1000
                    )

                    st.session_state.nearby_places = (
                        places
                    )

                if not places:

                    st.info(
                        "No nearby places found."
                    )

        except Exception as error:

            st.error(
                f"Nearby search failed: {error}"
            )


if st.session_state.nearby_places:

    st.markdown("#### 📍 Nearby Results")

    for place in (
        st.session_state.nearby_places
    ):

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

        maps_url = (
            create_google_maps_place_url(
                place["latitude"],
                place["longitude"]
            )
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

budget_col1, budget_col2 = (
    st.columns(2)
)

with budget_col1:

    stay_cost_per_day = (
        st.number_input(
            "🏨 Stay per Day ₹",
            min_value=0.0,
            value=1500.0,
            step=500.0
        )
    )

with budget_col2:

    food_cost_per_day = (
        st.number_input(
            "🍽️ Food per Day ₹",
            min_value=0.0,
            value=1000.0,
            step=500.0
        )
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

    try:

        fuel_cost = (
            st.session_state.fuel[
                "estimated_fuel_cost"
            ]
        )

        budget_result = calculate_trip_budget(
            total_budget=float(budget),
            travel_cost=float(fuel_cost),
            stay_cost=float(
                stay_cost_per_day * days
            ),
            food_cost=float(
                food_cost_per_day * days
            ),
            activity_cost=float(
                activity_cost
            ),
            other_cost=float(
                other_cost
            )
        )

        st.session_state.budget_result = (
            budget_result
        )

        st.markdown(
            "### 📊 Budget Summary"
        )

        budget_result1, budget_result2, budget_result3 = (
            st.columns(3)
        )

        with budget_result1:

            st.metric(
                "Total Budget",
                f"₹{budget_result['total_budget']:,.0f}"
            )

        with budget_result2:

            st.metric(
                "Estimated Cost",
                f"₹{budget_result['total_cost']:,.0f}"
            )

        with budget_result3:

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
                f"⚠️ Your trip exceeds budget by "
                f"₹{abs(budget_result['remaining_budget']):,.0f}"
            )

    except Exception as error:

        st.error(
            f"Budget calculation failed: {error}"
        )

else:

    st.info(
        "📍 Calculate route and fuel "
        "to see budget summary."
    )


# ============================================================
# CAMERA AI
# ============================================================

st.markdown("---")
st.markdown("### 📷 Tourist Camera AI")

camera_image = st.camera_input(
    "Take a photo of the place"
)

uploaded_image = st.file_uploader(
    "Or upload a travel image",
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

    try:

        image_result = (
            prepare_image_for_vision(
                selected_image
            )
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

                with st.spinner(
                    f"{voice_name} is analyzing..."
                ):

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

        else:

            st.error(
                image_result.get(
                    "message",
                    "Could not prepare image."
                )
            )

    except Exception as error:

        st.error(
            f"Image processing failed: {error}"
        )


# ============================================================
# CAMERA RESULT
# ============================================================

if st.session_state.camera_analysis:

    st.markdown(
        "### 📍 Place Analysis"
    )

    st.markdown(
        st.session_state.camera_analysis
    )

    if st.button(
        "🔊 Speak Place Analysis",
        key="speak_place_analysis"
    ):

        speak_text(
            st.session_state.camera_analysis,
            voice_name
        )


# ============================================================
# BUILD TOURIST AI CONTEXT
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

Fuel Type:
{fuel_type}

Mileage:
{mileage} km/L

Fuel Price:
₹{fuel_price}/L
"""

    if st.session_state.route:

        route = st.session_state.route

        context += f"""

Route Information:
Distance:
{route.get('distance_km', 'Unknown')} km

Driving Time:
{route.get('duration_minutes', 'Unknown')} minutes
"""

    if st.session_state.fuel:

        fuel = st.session_state.fuel

        context += f"""

Fuel Estimate:
Fuel Required:
{fuel['fuel_required_litres']} L

Fuel Cost:
₹{fuel['estimated_fuel_cost']}
"""

    if st.session_state.weather:

        weather = (
            st.session_state.weather
        )

        context += f"""

Latest Weather:
Temperature:
{weather['temperature']} °C

Feels Like:
{weather['feels_like']} °C

Humidity:
{weather['humidity']}%

Wind:
{weather['wind_speed']} km/h

Condition:
{weather_description(weather['weather_code'])}
"""

    if st.session_state.budget_result:

        budget_result = (
            st.session_state.budget_result
        )

        context += f"""

Budget Information:
Estimated Cost:
₹{budget_result['total_cost']}

Remaining:
₹{budget_result['remaining_budget']}
"""

    return context


# ============================================================
# TOURIST VOICE INPUT
# ============================================================

st.markdown("---")
st.markdown("### 🎤 Tourist AI Voice Input")

tourist_audio = st.audio_input(
    "Tap microphone and record your tourist question",
    key="tourist_voice_input"
)

if tourist_audio is not None:

    st.audio(
        tourist_audio
    )

    st.info(
        "🎤 Voice recorded successfully. "
        "Next we can connect Groq Whisper so "
        "your speech automatically becomes text."
    )


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
    height=110,
    key="tourist_question"
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

                mode_instruction_map = {

                    "Normal AI":
                    (
                        "Answer naturally, clearly "
                        "and helpfully."
                    ),

                    "Smart Trip Planner":
                    (
                        "Create practical and detailed "
                        "trip plans using route, budget, "
                        "fuel and weather information."
                    ),

                    "Travel Expert":
                    (
                        "Focus on attractions, culture, "
                        "local food, sightseeing and "
                        "useful travel tips."
                    ),

                    "Quick Mode":
                    (
                        "Give a short, direct and "
                        "useful answer."
                    )
                }

                mode_instruction = (
                    mode_instruction_map.get(
                        mode_name,
                        "Answer helpfully."
                    )
                )

                final_question = f"""
You are Tourist AI.

{context}

Mode Instruction:
{mode_instruction}

User Question:
{user_question}

Answer naturally in Tamil + English.

Use available trip information when useful.

Do not invent live prices,
weather or availability.
"""

                answer = ask_tourist_ai(
                    final_question,
                    voice=voice_name,
                    language="Tamil + English"
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
# TOURIST CHAT HISTORY
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
            key=f"speak_response_{index}"
        ):

            speak_text(
                chat["assistant"],
                chat["voice"]
            )


# ============================================================
# COMPLETE TRIP PLAN
# ============================================================

st.markdown("---")
st.markdown("### 🚀 Complete Trip Planner")

if st.button(
    "🚀 Create Complete Trip Plan",
    use_container_width=True
):

    if (
        not start_location.strip()
        or not destination.strip()
    ):

        st.warning(
            "Enter starting location and destination first."
        )

    else:

        try:

            with st.spinner(
                f"{voice_name} is creating "
                "your complete trip..."
            ):

                context = build_ai_context()

                prompt = f"""
You are Tourist AI.

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

Make the plan realistic and practical.

AI Personality:
{voice_name}

Respond naturally in Tamil + English.

Do not invent live prices,
weather or availability.
"""

                answer = ask_tourist_ai(
                    prompt,
                    voice=voice_name,
                    language="Tamil + English"
                )

                st.session_state.chat_history.append(
                    {
                        "user":
                        "🚀 Create Complete Trip Plan",

                        "assistant":
                        answer,

                        "voice":
                        voice_name
                    }
                )

                st.rerun()

        except Exception as error:

            st.error(
                f"Could not create trip plan: {error}"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🌍 Tourist AI • 💬 AI Chat • "
    "Plan smarter • Travel better"
)
