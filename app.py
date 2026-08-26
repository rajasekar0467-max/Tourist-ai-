app.py

import streamlit as st
import textwrap
import html
import time

from src.ai.groq_service import (
    ask_tourist_ai,
    ask_general_ai
)

from src.travel.fuel_calculator import calculate_fuel_cost
from src.maps.distance_service import get_route_distance
from src.maps.map_service import show_interactive_map

try:
    from src.maps.nearby_service import (
        get_nearby_places,
        create_google_maps_place_url
    )
    NEARBY_AVAILABLE = True

except Exception:
    NEARBY_AVAILABLE = False

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
    "page_mode": "tourist",
    "tourist_chat_history": [],
    "general_chat_history": [],
    "route": None,
    "fuel": None,
    "weather": None,
    "camera_analysis": None,
    "nearby_places": [],
    "budget_result": None,
    "chat_input_value": "",
    "tourist_voice_input": "",
    "general_voice_input": ""
}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# RESET FUNCTIONS
# ============================================================

def new_tourist_chat():

    st.session_state.tourist_chat_history = []
    st.session_state.route = None
    st.session_state.fuel = None
    st.session_state.weather = None
    st.session_state.camera_analysis = None
    st.session_state.nearby_places = []
    st.session_state.budget_result = None


def new_general_chat():

    st.session_state.general_chat_history = []
    st.session_state.chat_input_value = ""


# ============================================================
# SPEAK FUNCTION
# ============================================================

def speak_text(text, voice_name="JARVIS"):

    safe_text = (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "'")
        .replace("\n", " ")
        .replace('"', '\\"')
    )

    if voice_name == "JARVIS":

        rate = 0.92
        pitch = 0.88

    else:

        rate = 1.03
        pitch = 1.05

    html_code = f"""
    <script>

    const text = "{safe_text}";

    function startSpeaking() {{

        window.speechSynthesis.cancel();

        const utterance =
            new SpeechSynthesisUtterance(text);

        const voices =
            window.speechSynthesis.getVoices();

        let selectedVoice = null;

        if ("{voice_name}" === "JARVIS") {{

            selectedVoice = voices.find(
                voice =>
                /en-IN|en-GB|en-US/i.test(
                    voice.lang
                )
            );

        }} else {{

            selectedVoice = voices.find(
                voice =>
                /en-IN|en-US|en-GB/i.test(
                    voice.lang
                )
            );

        }}

        if (selectedVoice) {{

            utterance.voice =
                selectedVoice;

        }}

        utterance.rate = {rate};
        utterance.pitch = {pitch};
        utterance.volume = 1;

        window.speechSynthesis.speak(
            utterance
        );

    }}

    if (
        window.speechSynthesis
        .getVoices()
        .length === 0
    ) {{

        window.speechSynthesis
        .addEventListener(
            "voiceschanged",
            startSpeaking,
            {{ once: true }}
        );

    }} else {{

        startSpeaking();

    }}

    </script>
    """

    st.components.v1.html(
        html_code,
        height=0
    )


# ============================================================
# VOICE INPUT
# Browser Web Speech API
# ============================================================

def voice_input_component(component_id):

    voice_html = f"""
    <div style="
        font-family:Arial;
        padding:4px;
    ">

    <button id="mic-{component_id}"
    style="
        width:100%;
        border:none;
        border-radius:14px;
        padding:13px;
        font-size:16px;
        font-weight:600;
        cursor:pointer;
        background:#1d4ed8;
        color:white;
    ">
        🎤 Tap & Speak
    </button>

    <p id="status-{component_id}"
    style="
        text-align:center;
        color:#94a3b8;
        font-size:13px;
    ">
        Voice input ready
    </p>

    <script>

    const button =
        document.getElementById(
            "mic-{component_id}"
        );

    const status =
        document.getElementById(
            "status-{component_id}"
        );

    const Recognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!Recognition) {{

        status.innerText =
            "Voice recognition not supported in this browser.";

    }} else {{

        const recognition =
            new Recognition();

        recognition.continuous =
            false;

        recognition.interimResults =
            false;

        recognition.lang =
            "en-IN";

        button.onclick = () => {{

            recognition.start();

        }};

        recognition.onstart = () => {{

            button.innerText =
                "🔴 Listening...";

            status.innerText =
                "Speak now...";

        }};

        recognition.onresult = event => {{

            const text =
                event.results[0][0]
                .transcript;

            status.innerText =
                "You said: " + text;

            navigator.clipboard
            .writeText(text)
            .catch(() => {{}});

            button.innerText =
                "🎤 Tap & Speak";

        }};

        recognition.onerror = () => {{

            button.innerText =
                "🎤 Tap & Speak";

            status.innerText =
                "Voice input failed. Try again.";

        }};

        recognition.onend = () => {{

            button.innerText =
                "🎤 Tap & Speak";

        }};

    }}

    </script>

    </div>
    """

    st.components.v1.html(
        voice_html,
        height=110
    )


# ============================================================
# TYPING ANIMATION
# ============================================================

def animated_response(text):

    safe_text = html.escape(
        str(text)
    )

    animation_html = f"""
    <div class="ai-response-box"
    id="response-box">

    </div>

    <script>

    const fullText =
        `{safe_text}`;

    const box =
        document.getElementById(
            "response-box"
        );

    let index = 0;

    function typeText() {{

        if (
            index < fullText.length
        ) {{

            box.innerHTML +=
                fullText.charAt(index);

            index++;

            setTimeout(
                typeText,
                8
            );

        }}

    }}

    typeText();

    </script>
    """

    st.components.v1.html(
        animation_html,
        height=220,
        scrolling=True
    )


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    textwrap.dedent(
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
                    #121c31,
                    #070b12 55%
                );
            color: white;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 1.2rem;
            padding-bottom: 4rem;
        }

        .main-title {
            text-align:center;
            margin-bottom:20px;
        }

        .main-title h1 {
            font-size:42px;
            margin-bottom:4px;
        }

        .main-title p {
            color:#94a3b8;
            font-size:16px;
        }

        .glass-card {
            background:
                rgba(17,24,39,0.85);
            border:
                1px solid #263244;
            border-radius:20px;
            padding:20px;
            margin-bottom:15px;
        }

        .chat-user {
            background:#172033;
            border:1px solid #263244;
            padding:15px 18px;
            border-radius:
                18px 18px 4px 18px;
            margin-top:14px;
            margin-left:10%;
        }

        .chat-ai {
            background:#0f172a;
            border:1px solid #263244;
            padding:15px 18px;
            border-radius:
                18px 18px 18px 4px;
            margin-top:10px;
            margin-right:10%;
        }

        .thinking-wrap {
            display:flex;
            align-items:center;
            gap:10px;
            padding:15px;
            color:#cbd5e1;
        }

        .blue-ball {
            width:16px;
            height:16px;
            border-radius:50%;
            background:#3b82f6;
            animation:pulseBall 1s infinite;
            box-shadow:
                0 0 18px #3b82f6;
        }

        @keyframes pulseBall {

            0% {
                transform:scale(0.7);
                opacity:0.4;
            }

            50% {
                transform:scale(1.3);
                opacity:1;
            }

            100% {
                transform:scale(0.7);
                opacity:0.4;
            }

        }

        .ai-response-box {
            background:#0f172a;
            border:1px solid #263244;
            border-radius:18px;
            padding:18px;
            color:#e5e7eb;
            line-height:1.6;
            white-space:pre-wrap;
            min-height:80px;
        }

        .stButton > button {
            border-radius:14px;
            min-height:45px;
            font-weight:650;
        }

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            background:#111827;
            color:white;
            border-radius:13px;
        }

        .stChatInput textarea {
            background:#111827;
            color:white;
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
    [1, 2, 1]
)

with nav1:

    if st.button(
        "🌍 Tourist AI",
        use_container_width=True
    ):

        st.session_state.page_mode = (
            "tourist"
        )

        st.rerun()


with nav2:

    if st.button(
        "💬 Chat Mode",
        use_container_width=True
    ):

        st.session_state.page_mode = (
            "chat"
        )

        st.rerun()


with nav3:

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        if (
            st.session_state.page_mode
            == "chat"
        ):

            new_general_chat()

        else:

            new_tourist_chat()

        st.rerun()


# ============================================================
# GENERAL CHAT MODE
# ============================================================

if st.session_state.page_mode == "chat":

    st.markdown(
        """
        <div class="main-title">
            <h1>💬 AI Chat</h1>
            <p>
                Ask anything • Tamil • English • Coding • Study • Ideas
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    voice = st.radio(
        "AI Personality",
        [
            "🦾 JARVIS",
            "🕷️ EDY"
        ],
        horizontal=True,
        label_visibility="collapsed"
    )

    voice_name = (
        "JARVIS"
        if voice == "🦾 JARVIS"
        else "EDY"
    )

    st.caption(
        f"🤖 Current AI: {voice_name}"
    )

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    if not (
        st.session_state
        .general_chat_history
    ):

        st.markdown(
            """
            <div class="glass-card">
                <h3>Hey! 👋</h3>
                <p>
                    Naan general AI assistant.
                    Tourist questions mattum illa.
                    Coding, study, ideas, doubts,
                    anything ask pannalaam.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    for index, chat in enumerate(
        st.session_state
        .general_chat_history
    ):

        user_text = html.escape(
            str(chat["user"])
        )

        st.markdown(
            f"""
            <div class="chat-user">
                {user_text}
            </div>
            """,
            unsafe_allow_html=True
        )

        assistant_text = (
            chat["assistant"]
        )

        st.markdown(
            f"""
            <div class="chat-ai">
                {assistant_text}
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "🔊",
            key=f"general_speak_{index}"
        ):

            speak_text(
                assistant_text,
                chat.get(
                    "voice",
                    voice_name
                )
            )

    # --------------------------------------------------------
    # VOICE INPUT
    # --------------------------------------------------------

    with st.expander(
        "🎤 Voice Assistant"
    ):

        st.caption(
            "Tap microphone, speak, then paste the recognized text into chat."
        )

        voice_input_component(
            "general_voice"
        )

    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    user_message = st.chat_input(
        "Message AI..."
    )

    if user_message:

        st.markdown(
            f"""
            <div class="chat-user">
                {html.escape(user_message)}
            </div>
            """,
            unsafe_allow_html=True
        )

        thinking = st.empty()

        thinking.markdown(
            """
            <div class="thinking-wrap">
                <div class="blue-ball"></div>
                AI is thinking...
            </div>
            """,
            unsafe_allow_html=True
        )

        try:

            answer = ask_general_ai(
                user_message=user_message,
                voice=voice_name,
                language="Tamil + English",
                chat_history=
                st.session_state
                .general_chat_history
            )

            thinking.empty()

            animated_response(
                answer
            )

            st.session_state \
                .general_chat_history \
                .append(
                    {
                        "user":
                        user_message,

                        "assistant":
                        answer,

                        "voice":
                        voice_name
                    }
                )

        except Exception as error:

            thinking.empty()

            st.error(
                f"AI Error: {error}"
            )

    st.stop()


# ============================================================
# TOURIST AI PAGE
# ============================================================

st.markdown(
    """
    <div class="main-title">
        <h1>🌍 Tourist AI</h1>
        <p>
            Plan • Explore • Discover • Travel Smarter
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# VOICE SELECTION
# ============================================================

st.markdown(
    "### 🎙️ Choose Your AI"
)

voice = st.radio(
    "Voice",
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

st.info(
    f"🤖 {voice_name} — "
    f"{voice_description}"
)


# ============================================================
# AI MODE
# ============================================================

st.markdown(
    "### 🧠 AI Mode"
)

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

    "🤖 Normal AI":
        "Normal AI",

    "🧠 Smart Trip Planner":
        "Smart Trip Planner",

    "📍 Travel Expert":
        "Travel Expert",

    "⚡ Quick Mode":
        "Quick Mode"
}

mode_name = mode_map.get(
    ai_mode,
    "Normal AI"
)


# ============================================================
# TRIP DETAILS
# ============================================================

st.markdown("---")
st.markdown(
    "### ✈️ Plan Your Trip"
)

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

st.markdown(
    "### 🚗 Travel & Fuel"
)

f1, f2, f3 = st.columns(3)

with f1:

    fuel_type = st.selectbox(
        "⛽ Fuel Type",
        [
            "Petrol",
            "Diesel"
        ]
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
                "Calculating route... 🗺️"
            ):

                route = get_route_distance(
                    start_location,
                    destination
                )

                st.session_state.route = route

                st.session_state.fuel = (
                    calculate_fuel_cost(
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
                )

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

    st.markdown(
        "### 🗺️ Route Result"
    )

    r1, r2, r3 = st.columns(3)

    with r1:

        st.metric(
            "📍 One-way Distance",
            f"{distance:.1f} km"
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

    # GOOGLE MAPS DIRECT BUTTON

    google_maps_url = route.get(
        "google_maps_url"
    )

    if google_maps_url:

        st.link_button(
            "🗺️ Open Full Route in Google Maps",
            google_maps_url,
            use_container_width=True
        )

    try:

        show_interactive_map(
            route
        )

    except Exception as error:

        st.warning(
            f"Map display unavailable: {error}"
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

    st.markdown(
        "### 🌦️ Destination Weather"
    )

    if (
        latitude is None
        or longitude is None
    ):

        st.warning(
            "Destination coordinates unavailable."
        )

    elif st.button(
        "🌦️ Check Live Weather",
        use_container_width=True
    ):

        try:

            with st.spinner(
                "Getting weather..."
            ):

                st.session_state.weather = (
                    get_weather(
                        latitude,
                        longitude
                    )
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
            f"{weather.get('temperature', 'N/A')} °C"
        )

    with w2:

        st.metric(
            "🤒 Feels Like",
            f"{weather.get('feels_like', 'N/A')} °C"
        )

    with w3:

        st.metric(
            "💧 Humidity",
            f"{weather.get('humidity', 'N/A')}%"
        )

    with w4:

        st.metric(
            "💨 Wind",
            f"{weather.get('wind_speed', 'N/A')} km/h"
        )

    try:

        description = weather_description(
            weather.get(
                "weather_code"
            )
        )

        advice = get_weather_advice(
            weather
        )

        st.info(
            f"**{description}**\n\n"
            f"{advice}"
        )

    except Exception:

        pass


# ============================================================
# FUEL RESULT
# ============================================================

if st.session_state.fuel:

    fuel = st.session_state.fuel

    st.markdown(
        "### ⛽ Fuel Estimate"
    )

    f1, f2, f3 = st.columns(3)

    with f1:

        st.metric(
            "Fuel Type",
            fuel_type
        )

    with f2:

        st.metric(
            "Fuel Required",
            f"{fuel.get('fuel_required_litres', 0)} L"
        )

    with f3:

        st.metric(
            "Estimated Cost",
            f"₹{fuel.get('estimated_fuel_cost', 0):,.0f}"
        )


# ============================================================
# NEARBY PLACES
# ============================================================

if st.session_state.route:

    st.markdown("---")
    st.markdown(
        "### 📍 Discover Nearby Places"
    )

    if not NEARBY_AVAILABLE:

        st.warning(
            "Nearby service module is unavailable."
        )

    else:

        p1, p2 = st.columns(2)

        with p1:

            place_type = st.selectbox(
                "Find Nearby",
                [
                    "restaurant",
                    "hotel",
                    "cafe",
                    "food"
                ]
            )

        with p2:

            radius_km = st.selectbox(
                "Search Radius",
                [2, 5, 10, 15],
                index=1
            )

        if st.button(
            "🔍 Find Nearby Places",
            use_container_width=True
        ):

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

                try:

                    with st.spinner(
                        "Searching nearby places..."
                    ):

                        places = (
                            get_nearby_places(
                                latitude,
                                longitude,
                                place_type=place_type,
                                radius=int(
                                    radius_km * 1000
                                )
                            )
                        )

                        st.session_state \
                            .nearby_places = (
                                places or []
                            )

                    if not places:

                        st.info(
                            "No places found. Try increasing the search radius."
                        )

                except Exception as error:

                    st.error(
                        "Nearby search temporarily failed. "
                        f"Error: {error}"
                    )


if st.session_state.nearby_places:

    st.markdown(
        "#### 📍 Nearby Results"
    )

    for index, place in enumerate(
        st.session_state.nearby_places
    ):

        place_name = html.escape(
            str(
                place.get(
                    "name",
                    "Unknown Place"
                )
            )
        )

        address = html.escape(
            str(
                place.get(
                    "address",
                    "Address unavailable"
                )
            )
        )

        distance_km = place.get(
            "distance_km",
            "?"
        )

        category = place.get(
            "category",
            "place"
        )

        st.markdown(
            f"""
            <div class="glass-card">
                <h4>📍 {place_name}</h4>
                <p>
                    📏 {distance_km} km away<br>
                    🏷️ {category}<br>
                    📌 {address}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        try:

            maps_url = (
                create_google_maps_place_url(
                    place.get("latitude"),
                    place.get("longitude")
                )
            )

            st.link_button(
                f"🗺️ Open {place_name} in Google Maps",
                maps_url,
                key=f"place_map_{index}",
                use_container_width=True
            )

        except Exception:

            pass


# ============================================================
# BUDGET
# ============================================================

st.markdown("---")
st.markdown(
    "### 💰 Trip Budget"
)

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

    try:

        fuel_cost = float(
            st.session_state.fuel.get(
                "estimated_fuel_cost",
                0
            )
        )

        budget_result = (
            calculate_trip_budget(
                total_budget=float(budget),
                travel_cost=fuel_cost,
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
        )

        st.session_state.budget_result = (
            budget_result
        )

        br1, br2, br3 = st.columns(3)

        with br1:

            st.metric(
                "Total Budget",
                f"₹{budget_result.get('total_budget', 0):,.0f}"
            )

        with br2:

            st.metric(
                "Estimated Cost",
                f"₹{budget_result.get('total_cost', 0):,.0f}"
            )

        with br3:

            st.metric(
                "Remaining",
                f"₹{budget_result.get('remaining_budget', 0):,.0f}"
            )

    except Exception as error:

        st.warning(
            f"Budget calculation unavailable: {error}"
        )


# ============================================================
# CAMERA AI
# ============================================================

st.markdown("---")
st.markdown(
    "### 📷 Tourist Camera AI"
)

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

        if image_result.get(
            "success"
        ):

            st.image(
                image_result.get("image"),
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

                    st.session_state \
                        .camera_analysis = (
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
            f"Camera AI failed: {error}"
        )


if st.session_state.camera_analysis:

    st.markdown(
        "### 📍 Place Analysis"
    )

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

Route:
Distance: {route.get('distance_km', 'Unknown')} km
Driving Time: {route.get('duration_minutes', 'Unknown')} minutes
"""

    if st.session_state.fuel:

        fuel = st.session_state.fuel

        context += f"""

Fuel:
Required: {fuel.get('fuel_required_litres', 'Unknown')} L
Cost: ₹{fuel.get('estimated_fuel_cost', 'Unknown')}
"""

    if st.session_state.weather:

        weather = st.session_state.weather

        context += f"""

Weather:
Temperature: {weather.get('temperature', 'Unknown')} °C
Humidity: {weather.get('humidity', 'Unknown')}%
"""

    return context


# ============================================================
# ASK TOURIST AI
# ============================================================

st.markdown("---")
st.markdown(
    "### 🧠 Ask Tourist AI"
)

with st.expander(
    "🎤 Voice Input"
):

    voice_input_component(
        "tourist_voice"
    )

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

            context = build_ai_context()

            mode_instruction_map = {

                "Normal AI":
                    "Answer naturally and helpfully.",

                "Smart Trip Planner":
                    (
                        "Create detailed and practical "
                        "trip plans using available data."
                    ),

                "Travel Expert":
                    (
                        "Focus on attractions, culture, "
                        "food and travel tips."
                    ),

                "Quick Mode":
                    (
                        "Give short and useful answers."
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

Mode:
{mode_instruction}

User Question:
{user_question}

Reply naturally in Tamil + English.
Use trip information when useful.
"""

            thinking = st.empty()

            thinking.markdown(
                """
                <div class="thinking-wrap">
                    <div class="blue-ball"></div>
                    Tourist AI is thinking...
                </div>
                """,
                unsafe_allow_html=True
            )

            answer = ask_tourist_ai(
                final_question,
                voice=voice_name,
                language="Tamil + English",
                chat_history=
                st.session_state
                .tourist_chat_history
            )

            thinking.empty()

            st.session_state \
                .tourist_chat_history \
                .append(
                    {
                        "user":
                        user_question,

                        "assistant":
                        answer,

                        "voice":
                        voice_name
                    }
                )

            st.rerun()

        except Exception as error:

            st.error(
                f"Tourist AI Error: {error}"
            )


# ============================================================
# TOURIST CHAT HISTORY
# ============================================================

if st.session_state.tourist_chat_history:

    st.markdown("---")
    st.markdown(
        "### 💬 Tourist AI Chat"
    )

    for index, chat in enumerate(
        st.session_state
        .tourist_chat_history
    ):

        user_text = html.escape(
            str(chat.get("user", ""))
        )

        st.markdown(
            f"""
            <div class="chat-user">
                {user_text}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="chat-ai">
                {chat.get("assistant", "")}
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "🔊 Speak Response",
            key=f"tourist_speak_{index}"
        ):

            speak_text(
                chat.get(
                    "assistant",
                    ""
                ),
                chat.get(
                    "voice",
                    voice_name
                )
            )


# ============================================================
# COMPLETE TRIP PLAN
# ============================================================

st.markdown("---")
st.markdown(
    "### 🚀 Complete Trip Planner"
)

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

            context = build_ai_context()

            prompt = f"""
You are Tourist AI.

{context}

Create a complete practical tourist trip plan.

Include:

1. Route summary
2. Weather advice
3. Day-by-day itinerary
4. Important places
5. Food suggestions
6. Stay suggestions
7. Budget planning
8. Fuel tips
9. Things to carry
10. Important travel notes

Respond naturally in Tamil + English.
"""

            thinking = st.empty()

            thinking.markdown(
                """
                <div class="thinking-wrap">
                    <div class="blue-ball"></div>
                    Creating your trip plan...
                </div>
                """,
                unsafe_allow_html=True
            )

            answer = ask_tourist_ai(
                prompt,
                voice=voice_name,
                language="Tamil + English",
                chat_history=
                st.session_state
                .tourist_chat_history
            )

            thinking.empty()

            st.session_state \
                .tourist_chat_history \
                .append(
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
    "🌍 Tourist AI • Plan smarter • Travel better"
)
