import streamlit as st
import textwrap
import json
import time

from groq import Groq

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
    "page_mode": "tourist",
    "chat_history": [],
    "general_chat_history": [],
    "route": None,
    "fuel": None,
    "weather": None,
    "camera_analysis": None,
    "nearby_places": [],
    "budget_result": None,
    "auto_speak_text": None,
    "auto_speak_voice": "JARVIS",
    "voice_status": "",
    "last_voice_hash": None
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
    st.session_state.auto_speak_text = None
    st.session_state.voice_status = ""
    st.session_state.last_voice_hash = None

    st.rerun()


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():

    try:

        api_key = st.secrets["GROQ_API_KEY"]

    except Exception:

        raise ValueError(
            "GROQ_API_KEY not found in Streamlit Secrets."
        )

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is empty."
        )

    return Groq(api_key=api_key)


# ============================================================
# GENERAL AI
# ============================================================

def ask_general_ai(
    user_message,
    voice_name="JARVIS",
    history=None
):

    if not user_message.strip():

        return "Please say or type something first."

    client = get_groq_client()

    if voice_name == "JARVIS":

        personality = """
You are JARVIS.

You are calm, intelligent, helpful and professional.
You can answer questions about any general topic.

Speak naturally.
Do not pretend to have real-world powers.
"""

    else:

        personality = """
You are EDY.

You are friendly, energetic, casual and helpful.
You can answer questions about any general topic.

Speak naturally like a smart AI friend.
"""

    system_prompt = f"""
{personality}

You are a general purpose AI assistant.

You are NOT limited to tourism.

You can help with:
- Study
- Coding
- Technology
- General knowledge
- Ideas
- Writing
- Travel
- Daily questions
- Explanations
- Problem solving

Language rules:
- Understand Tamil written in English letters.
- Understand Tamil script.
- Understand English.
- Understand mixed Tamil + English.
- Reply naturally in the user's preferred language.
- If the user speaks Tanglish, Tanglish is allowed.
- Be clear and useful.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if history:

        for chat in history[-10:]:

            user_text = chat.get("user", "")
            assistant_text = chat.get("assistant", "")

            if user_text:

                messages.append(
                    {
                        "role": "user",
                        "content": user_text
                    }
                )

            if assistant_text:

                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_text
                    }
                )

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.7,
        max_completion_tokens=1200
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    return answer.strip()


# ============================================================
# AUDIO TO TEXT
# ============================================================

def transcribe_audio(audio_file):

    if audio_file is None:
        return ""

    try:

        audio_bytes = audio_file.getvalue()

        if not audio_bytes:
            return ""

        client = get_groq_client()

        response = client.audio.transcriptions.create(
            file=(
                "voice_input.wav",
                audio_bytes,
                "audio/wav"
            ),
            model="whisper-large-v3-turbo",
            response_format="json",
            temperature=0.0
        )

        text = getattr(
            response,
            "text",
            ""
        )

        if not text:
            try:
                text = response["text"]
            except Exception:
                text = ""

        return str(text).strip()

    except Exception as error:

        st.error(
            f"Voice recognition failed: {error}"
        )

        return ""


# ============================================================
# SPEAK FUNCTION
# ============================================================

def speak_text(text, voice_name):

    if not text:
        return

    clean_text = str(text)

    if voice_name == "JARVIS":

        rate = 0.92
        pitch = 0.88

    else:

        rate = 1.04
        pitch = 1.05

    safe_text = json.dumps(
        clean_text
    )

    html = f"""
    <script>

    const text = {safe_text};

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
                /david|mark|daniel|alex|male/i
                .test(voice.name)
            );

        }} else {{

            selectedVoice = voices.find(
                voice =>
                /samantha|zira|karen|female/i
                .test(voice.name)
            );

        }}

        if (!selectedVoice) {{

            selectedVoice = voices.find(
                voice =>
                /en-IN|ta-IN|en-US|en-GB/i
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
            startSpeaking,
            {{ once: true }}
        );

    }} else {{

        startSpeaking();

    }}

    </script>
    """

    st.components.v1.html(
        html,
        height=0
    )


# ============================================================
# AUTO SPEAK
# ============================================================

def trigger_auto_speak(
    text,
    voice_name
):

    st.session_state.auto_speak_text = text
    st.session_state.auto_speak_voice = voice_name


def run_auto_speak():

    text = st.session_state.get(
        "auto_speak_text"
    )

    if text:

        speak_text(
            text,
            st.session_state.auto_speak_voice
        )

        st.session_state.auto_speak_text = None


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
            background: #08111f;
            color: #f8fafc !important;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 1rem;
            padding-bottom: 4rem;
        }

        /* ================================================
           FIX INVISIBLE / BLACK TEXT
        ================================================= */

        .stApp,
        .stMarkdown,
        .stMarkdown p,
        .stMarkdown span,
        .stMarkdown li,
        .stMarkdown div,
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6 {
            color: #f8fafc !important;
        }

        p, span, div, label {
            color: #f8fafc;
        }

        /* ================================================
           TITLE
        ================================================= */

        .title {
            text-align: center;
            padding: 20px 10px;
        }

        .title h1 {
            font-size: 46px;
            margin-bottom: 5px;
            color: #ffffff !important;
        }

        .title p {
            color: #aeb8c8 !important;
            font-size: 16px;
        }

        /* ================================================
           CARDS
        ================================================= */

        .card {
            background: #111b2e;
            border: 1px solid #2a3850;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 15px;
            color: #ffffff !important;
        }

        .feature-card {
            background: #111b2e;
            border: 1px solid #2a3850;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 15px;
            color: #ffffff !important;
        }

        /* ================================================
           CHAT
        ================================================= */

        .chat-user {
            background: #1d2b42;
            border: 1px solid #334866;
            color: #ffffff !important;
            padding: 16px 18px;
            border-radius: 20px 20px 5px 20px;
            margin: 12px 0 8px auto;
            max-width: 82%;
        }

        .chat-ai {
            background: #111b2e;
            border: 1px solid #293a54;
            color: #ffffff !important;
            padding: 16px 18px;
            border-radius: 20px 20px 20px 5px;
            margin: 8px auto 12px 0;
            max-width: 88%;
        }

        .chat-user *,
        .chat-ai * {
            color: #ffffff !important;
        }

        /* ================================================
           BUTTONS
        ================================================= */

        .stButton > button {
            border-radius: 14px;
            min-height: 46px;
            font-weight: 600;
            color: #ffffff !important;
            background: #17243a;
            border: 1px solid #314564;
        }

        .stButton > button:hover {
            border-color: #3b82f6;
        }

        /* ================================================
           INPUTS
        ================================================= */

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            background: #111b2e !important;
            color: #ffffff !important;
            border-radius: 12px;
            border: 1px solid #334155 !important;
        }

        textarea::placeholder,
        input::placeholder {
            color: #94a3b8 !important;
        }

        /* ================================================
           CHAT INPUT
        ================================================= */

        [data-testid="stChatInput"] {
            background: #111b2e !important;
            border-radius: 18px;
        }

        [data-testid="stChatInput"] textarea {
            color: #ffffff !important;
        }

        /* ================================================
           BLUE THINKING BALL
        ================================================= */

        .thinking-area {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 15px 5px;
        }

        .blue-ball {
            width: 16px;
            height: 16px;
            background: #3b82f6;
            border-radius: 50%;
            animation: pulseBall 1s infinite ease-in-out;
            box-shadow: 0 0 18px #3b82f6;
        }

        .thinking-text {
            color: #dbeafe !important;
            font-size: 15px;
        }

        @keyframes pulseBall {

            0% {
                transform: scale(0.7);
                opacity: 0.4;
            }

            50% {
                transform: scale(1.25);
                opacity: 1;
            }

            100% {
                transform: scale(0.7);
                opacity: 0.4;
            }
        }

        /* ================================================
           VOICE CARD
        ================================================= */

        .voice-card {
            background: #0f1b2d;
            border: 1px solid #2c4264;
            border-radius: 18px;
            padding: 15px;
            margin-top: 10px;
            color: #ffffff !important;
        }

        /* ================================================
           METRICS
        ================================================= */

        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }

        [data-testid="stMetricLabel"] {
            color: #cbd5e1 !important;
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

        st.session_state.page_mode = "tourist"
        st.rerun()

with nav3:

    if st.button(
        "💬 Chat Mode",
        use_container_width=True
    ):

        st.session_state.page_mode = "chat"
        st.rerun()


# ============================================================
# VOICE SELECTION
# ============================================================

st.markdown("---")
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
# THINKING ANIMATION
# ============================================================

def show_thinking(message):

    st.markdown(
        f"""
        <div class="thinking-area">
            <div class="blue-ball"></div>
            <div class="thinking-text">
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# GENERAL CHAT MODE
# ============================================================

if st.session_state.page_mode == "chat":

    st.markdown(
        """
        <div class="title">
            <h1>💬 AI Chat</h1>
            <p>Ask anything • Tamil • English • Tanglish</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="card">
            <h3>Vanakkam! 👋</h3>
            <p>
                Enkitta edhu venalum kekkalam.
                Study, coding, technology, ideas,
                travel, general questions — anything!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    for index, chat in enumerate(
        st.session_state.general_chat_history
    ):

        with st.chat_message(
            "user",
            avatar=None
        ):

            st.markdown(
                chat["user"]
            )

        with st.chat_message(
            "assistant",
            avatar=None
        ):

            st.markdown(
                chat["assistant"]
            )

            if st.button(
                "🔊 Speak",
                key=f"general_speak_{index}"
            ):

                speak_text(
                    chat["assistant"],
                    chat.get(
                        "voice",
                        voice_name
                    )
                )

    # ========================================================
    # VOICE INPUT
    # ========================================================

    st.markdown("---")
    st.markdown(
        "### 🎤 Voice Assistant"
    )

    st.caption(
        "Record your voice → stop recording → AI automatically replies"
    )

    voice_audio = st.audio_input(
        "🎤 Speak in Tamil, English or Tanglish",
        key="general_voice_input"
    )

    if voice_audio is not None:

        audio_bytes = voice_audio.getvalue()

        audio_hash = str(
            hash(audio_bytes)
        )

        if (
            audio_hash
            != st.session_state.last_voice_hash
        ):

            st.session_state.last_voice_hash = audio_hash

            with st.spinner("🎤 Understanding your voice..."):

                voice_text = transcribe_audio(
                    voice_audio
                )

            if voice_text:

                st.success(
                    f"🎤 You said: {voice_text}"
                )

                thinking_box = st.empty()

                with thinking_box.container():

                    show_thinking(
                        f"{voice_name} is thinking..."
                    )

                try:

                    answer = ask_general_ai(
                        voice_text,
                        voice_name,
                        st.session_state.general_chat_history
                    )

                    thinking_box.empty()

                    st.session_state.general_chat_history.append(
                        {
                            "user": voice_text,
                            "assistant": answer,
                            "voice": voice_name
                        }
                    )

                    trigger_auto_speak(
                        answer,
                        voice_name
                    )

                    st.rerun()

                except Exception as error:

                    thinking_box.empty()

                    st.error(
                        f"AI Error: {error}"
                    )

    # ========================================================
    # TEXT CHAT INPUT
    # ========================================================

    user_message = st.chat_input(
        "Message AI..."
    )

    if user_message:

        with st.chat_message(
            "user",
            avatar=None
        ):

            st.markdown(
                user_message
            )

        thinking_box = st.empty()

        with thinking_box.container():

            show_thinking(
                f"{voice_name} is thinking..."
            )

        try:

            answer = ask_general_ai(
                user_message,
                voice_name,
                st.session_state.general_chat_history
            )

            thinking_box.empty()

            with st.chat_message(
                "assistant",
                avatar=None
            ):

                placeholder = st.empty()

                displayed = ""

                for character in answer:

                    displayed += character

                    placeholder.markdown(
                        displayed + "▌"
                    )

                    time.sleep(0.003)

                placeholder.markdown(
                    displayed
                )

            st.session_state.general_chat_history.append(
                {
                    "user": user_message,
                    "assistant": answer,
                    "voice": voice_name
                }
            )

            trigger_auto_speak(
                answer,
                voice_name
            )

        except Exception as error:

            thinking_box.empty()

            st.error(
                f"AI Error: {error}"
            )


# ============================================================
# TOURIST AI MODE
# ============================================================

else:

    st.markdown(
        """
        <div class="title">
            <h1>🌍 Tourist AI</h1>
            <p>Plan • Explore • Discover • Travel Smarter</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # AI MODE
    # ========================================================

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


    # ========================================================
    # TRIP DETAILS
    # ========================================================

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


    # ========================================================
    # FUEL
    # ========================================================

    st.markdown("### 🚗 Travel & Fuel")

    fuel_col1, fuel_col2, fuel_col3 = (
        st.columns(3)
    )

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


    # ========================================================
    # ROUTE
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
                    "Calculating route... 🗺️"
                ):

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


    # ========================================================
    # ROUTE RESULT
    # ========================================================

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

        except Exception as error:

            st.warning(
                f"Interactive map unavailable: {error}"
            )

        google_maps_url = route.get(
            "google_maps_url"
        )

        if google_maps_url:

            st.link_button(
                "🗺️ Open Full Route in Google Maps",
                google_maps_url,
                use_container_width=True
            )


    # ========================================================
    # WEATHER
    # ========================================================

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
            latitude is not None
            and longitude is not None
        ):

            if st.button(
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

                    st.success(
                        "Weather loaded!"
                    )

                except Exception as error:

                    st.error(
                        f"Weather unavailable: {error}"
                    )

        else:

            st.warning(
                "Destination coordinates unavailable."
            )


    # ========================================================
    # WEATHER RESULT
    # ========================================================

    if st.session_state.weather:

        weather = (
            st.session_state.weather
        )

        w1, w2, w3, w4 = (
            st.columns(4)
        )

        with w1:

            st.metric(
                "🌡️ Temperature",
                f"{weather.get('temperature', '--')} °C"
            )

        with w2:

            st.metric(
                "🤒 Feels Like",
                f"{weather.get('feels_like', '--')} °C"
            )

        with w3:

            st.metric(
                "💧 Humidity",
                f"{weather.get('humidity', '--')}%"
            )

        with w4:

            st.metric(
                "💨 Wind",
                f"{weather.get('wind_speed', '--')} km/h"
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
                f"**{description}**\n\n{advice}"
            )

        except Exception:

            pass


    # ========================================================
    # FUEL RESULT
    # ========================================================

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


    # ========================================================
    # NEARBY PLACES
    # ========================================================

    if st.session_state.route:

        st.markdown("---")
        st.markdown(
            "### 📍 Discover Nearby Places"
        )

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
                        "Searching nearby places..."
                    ):

                        places = get_nearby_places(
                            float(latitude),
                            float(longitude),
                            place_type=place_type,
                            radius=int(
                                radius_km * 1000
                            )
                        )

                        st.session_state.nearby_places = (
                            places
                        )

                    if places:

                        st.success(
                            f"{len(places)} places found!"
                        )

                    else:

                        st.info(
                            "No places found. Try increasing the radius."
                        )

            except Exception as error:

                st.error(
                    f"Nearby search failed: {error}"
                )

                st.info(
                    "The public map server may be temporarily busy. Please try again."
                )


    if st.session_state.nearby_places:

        st.markdown(
            "#### 📍 Nearby Results"
        )

        for index, place in enumerate(
            st.session_state.nearby_places
        ):

            name = place.get(
                "name",
                "Unknown Place"
            )

            distance_km = place.get(
                "distance_km",
                "?"
            )

            category = place.get(
                "category",
                "place"
            )

            address = place.get(
                "address",
                "Address unavailable"
            )

            latitude = place.get(
                "latitude"
            )

            longitude = place.get(
                "longitude"
            )

            st.markdown(
                f"""
                <div class="card">
                    <h4>📍 {name}</h4>
                    <p>
                        📏 {distance_km} km away
                        <br>
                        🏷️ {category}
                        <br>
                        📌 {address}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if (
                latitude is not None
                and longitude is not None
            ):

                try:

                    maps_url = (
                        create_google_maps_place_url(
                            latitude,
                            longitude
                        )
                    )

                    st.link_button(
                        f"🗺️ Open {name} in Google Maps",
                        maps_url,
                        key=f"map_place_{index}",
                        use_container_width=True
                    )

                except Exception:

                    pass


    # ========================================================
    # BUDGET
    # ========================================================

    st.markdown("---")
    st.markdown(
        "### 💰 Trip Budget"
    )

    b1, b2 = st.columns(2)

    with b1:

        stay_cost_per_day = (
            st.number_input(
                "🏨 Stay per Day ₹",
                min_value=0.0,
                value=1500.0,
                step=500.0
            )
        )

    with b2:

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
                st.session_state.fuel.get(
                    "estimated_fuel_cost",
                    0
                )
            )

            budget_result = (
                calculate_trip_budget(
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
            )

            st.session_state.budget_result = (
                budget_result
            )

            st.markdown(
                "### 📊 Budget Summary"
            )

            x1, x2, x3 = st.columns(3)

            with x1:

                st.metric(
                    "Total Budget",
                    f"₹{budget_result.get('total_budget', 0):,.0f}"
                )

            with x2:

                st.metric(
                    "Estimated Cost",
                    f"₹{budget_result.get('total_cost', 0):,.0f}"
                )

            with x3:

                st.metric(
                    "Remaining",
                    f"₹{budget_result.get('remaining_budget', 0):,.0f}"
                )

            if budget_result.get(
                "within_budget",
                False
            ):

                st.success(
                    "✅ Your trip is within budget!"
                )

            else:

                remaining = (
                    budget_result.get(
                        "remaining_budget",
                        0
                    )
                )

                st.warning(
                    f"⚠️ Budget exceeds by ₹{abs(remaining):,.0f}"
                )

        except Exception as error:

            st.error(
                f"Budget calculation failed: {error}"
            )


    # ========================================================
    # CAMERA AI
    # ========================================================

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
                "success",
                False
            ):

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


    # ========================================================
    # BUILD AI CONTEXT
    # ========================================================

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

Fuel Estimate:
Fuel required: {fuel.get('fuel_required_litres', 0)} L
Fuel cost: ₹{fuel.get('estimated_fuel_cost', 0)}
"""

        if st.session_state.weather:

            weather = (
                st.session_state.weather
            )

            context += f"""

Weather:
Temperature: {weather.get('temperature', 'Unknown')} °C
Humidity: {weather.get('humidity', 'Unknown')}%
"""

        return context


    # ========================================================
    # TOURIST VOICE INPUT
    # ========================================================

    st.markdown("---")
    st.markdown(
        "### 🎤 Ask Tourist AI by Voice"
    )

    st.caption(
        "Speak Tamil / English / Tanglish → AI automatically replies"
    )

    tourist_voice_audio = st.audio_input(
        "🎤 Record your question",
        key="tourist_voice_input"
    )

    if tourist_voice_audio is not None:

        audio_bytes = (
            tourist_voice_audio.getvalue()
        )

        audio_hash = (
            "tourist_" +
            str(hash(audio_bytes))
        )

        if (
            audio_hash
            != st.session_state.last_voice_hash
        ):

            st.session_state.last_voice_hash = (
                audio_hash
            )

            with st.spinner(
                "🎤 Understanding your voice..."
            ):

                voice_question = (
                    transcribe_audio(
                        tourist_voice_audio
                    )
                )

            if voice_question:

                st.success(
                    f"🎤 You said: {voice_question}"
                )

                try:

                    thinking_box = st.empty()

                    with thinking_box.container():

                        show_thinking(
                            f"{voice_name} is planning..."
                        )

                    context = build_ai_context()

                    final_question = f"""
You are Tourist AI.

{context}

User Question:
{voice_question}

Answer naturally in Tamil + English.
Use available trip data when useful.
"""

                    answer = ask_tourist_ai(
                        final_question,
                        voice=voice_name,
                        language="Tamil + English",
                        chat_history=st.session_state.chat_history
                    )

                    thinking_box.empty()

                    st.session_state.chat_history.append(
                        {
                            "user": voice_question,
                            "assistant": answer,
                            "voice": voice_name
                        }
                    )

                    trigger_auto_speak(
                        answer,
                        voice_name
                    )

                    st.rerun()

                except Exception as error:

                    thinking_box.empty()

                    st.error(
                        f"Tourist AI Error: {error}"
                    )


    # ========================================================
    # TOURIST TEXT INPUT
    # ========================================================

    st.markdown("---")
    st.markdown(
        "### 🧠 Ask Tourist AI"
    )

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
                "Please enter or speak a question."
            )

        else:

            try:

                thinking_box = st.empty()

                with thinking_box.container():

                    show_thinking(
                        f"{voice_name} is thinking..."
                    )

                context = build_ai_context()

                final_question = f"""
You are Tourist AI.

{context}

User Question:
{user_question}

Answer naturally in Tamil + English.
Use available trip information when useful.
Do not invent live prices or availability.
"""

                answer = ask_tourist_ai(
                    final_question,
                    voice=voice_name,
                    language="Tamil + English",
                    chat_history=st.session_state.chat_history
                )

                thinking_box.empty()

                st.session_state.chat_history.append(
                    {
                        "user": user_question,
                        "assistant": answer,
                        "voice": voice_name
                    }
                )

                trigger_auto_speak(
                    answer,
                    voice_name
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"❌ Tourist AI Error: {error}"
                )


    # ========================================================
    # TOURIST CHAT HISTORY
    # ========================================================

    if st.session_state.chat_history:

        st.markdown("---")
        st.markdown(
            "### 💬 Tourist AI Chat"
        )

        for index, chat in enumerate(
            st.session_state.chat_history
        ):

            with st.chat_message(
                "user",
                avatar=None
            ):

                st.markdown(
                    chat["user"]
                )

            with st.chat_message(
                "assistant",
                avatar=None
            ):

                st.markdown(
                    chat["assistant"]
                )

                if st.button(
                    "🔊 Speak Response",
                    key=f"tourist_speak_{index}"
                ):

                    speak_text(
                        chat["assistant"],
                        chat.get(
                            "voice",
                            voice_name
                        )
                    )


    # ========================================================
    # COMPLETE TRIP PLAN
    # ========================================================

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

                thinking_box = st.empty()

                with thinking_box.container():

                    show_thinking(
                        f"{voice_name} is creating your trip..."
                    )

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
8. Fuel and travel tips
9. Things to carry
10. Important travel notes

Respond naturally in Tamil + English.
"""

                answer = ask_tourist_ai(
                    prompt,
                    voice=voice_name,
                    language="Tamil + English",
                    chat_history=st.session_state.chat_history
                )

                thinking_box.empty()

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

                trigger_auto_speak(
                    answer,
                    voice_name
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Could not create trip plan: {error}"
                )


    # ========================================================
    # FOOTER
    # ========================================================

    st.markdown("---")

    st.caption(
        "🌍 Tourist AI • Plan smarter • Travel better"
    )


# ============================================================
# RUN AUTO SPEECH LAST
# ============================================================

run_auto_speak()
