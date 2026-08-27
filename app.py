import streamlit as st
import json
import time
import hashlib
import requests
import base64

from groq import Groq

from src.voice_component import voice_assistant_component

from src.ai.groq_service import (
    ask_tourist_ai,
    ask_general_ai
)

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
    "friday_history": [],

    "route": None,
    "fuel": None,
    "weather": None,
    "nearby_places": [],
    "camera_analysis": None,

    "last_voice_hash": None,

    "friday_status": "READY TO LISTEN",
    "friday_last_answer": "",
    "friday_audio": "",

    "friday_running": False,
    "friday_last_event": "",

    "voice_speed": 1.0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():

    api_key = st.secrets.get(
        "GROQ_API_KEY",
        ""
    )

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found in Streamlit Secrets."
        )

    return Groq(
        api_key=api_key
    )


# ============================================================
# ELEVENLABS CONFIG
# ============================================================

def get_elevenlabs_config():

    api_key = st.secrets.get(
        "ELEVENLABS_API_KEY",
        ""
    )

    voice_id = st.secrets.get(
        "ELEVENLABS_VOICE_ID",
        ""
    )

    if not api_key:
        raise ValueError(
            "ELEVENLABS_API_KEY not found in Secrets."
        )

    if not voice_id:
        raise ValueError(
            "ELEVENLABS_VOICE_ID not found in Secrets."
        )

    return api_key, voice_id


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
    st.session_state.nearby_places = []
    st.session_state.camera_analysis = None

    st.session_state.last_voice_hash = None

    st.session_state.friday_status = "READY TO LISTEN"
    st.session_state.friday_last_answer = ""
    st.session_state.friday_audio = ""
    st.session_state.friday_running = False
    st.session_state.friday_last_event = ""

    st.rerun()


# ============================================================
# ELEVENLABS PREMIUM TTS
# ============================================================

def generate_friday_voice(text):

    if not text:
        return ""

    try:

        api_key, voice_id = get_elevenlabs_config()

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
            "text": str(text),
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.75,
                "style": 0.35,
                "use_speaker_boost": True
            }
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(response.text)

        return base64.b64encode(
            response.content
        ).decode()

    except Exception as error:

        st.session_state.friday_status = "VOICE ERROR"

        st.error(
            f"🔊 FRIDAY voice error: {error}"
        )

        return ""


# ============================================================
# FRIDAY AI
# ============================================================

def ask_friday(user_message):

    friday_prompt = f"""
You are FRIDAY, a premium intelligent personal AI assistant.

Personality:
- Warm
- Intelligent
- Friendly
- Emotionally aware
- Calm
- Natural
- Helpful

Language:
- Understand Tamil
- Understand English
- Understand Tanglish
- Reply naturally in the user's language style.
- Tamil-English mixing is allowed naturally.

Style:
- Speak conversationally.
- Do not sound robotic.
- Be concise unless detail is needed.
- For casual conversation, be warm and natural.
- For serious questions, be calm and supportive.

User:
{user_message}

Reply as FRIDAY.
"""

    return ask_general_ai(
        friday_prompt,
        voice="FRIDAY",
        language="Tamil + English",
        chat_history=st.session_state.friday_history
    )


# ============================================================
# TYPING ANIMATION
# ============================================================

def type_response(answer):

    placeholder = st.empty()

    displayed = ""

    for character in answer:

        displayed += character

        placeholder.markdown(
            displayed + "▌"
        )

        time.sleep(0.002)

    placeholder.markdown(displayed)


# ============================================================
# THINKING
# ============================================================

def show_thinking(text):

    st.markdown(
        f"""
        <div class="thinking">
            <div class="thinking-orb"></div>
            <span>{text}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


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
        color: #f8fafc !important;
    }

    .main-title {
        text-align: center;
        padding: 20px;
    }

    .main-title h1 {
        color: white !important;
        font-size: 42px;
    }

    .main-title p {
        color: #9ca3af !important;
    }

    .stButton button {

        background:
            rgba(18, 35, 30, 0.9) !important;

        color:
            white !important;

        border:
            1px solid #245c4a !important;

        border-radius:
            14px !important;

        min-height:
            46px;

        font-weight:
            600;
    }

    .stButton button:hover {

        border-color:
            #20d489 !important;

        box-shadow:
            0 0 18px
            rgba(32, 212, 137, 0.35);
    }

    .card {

        background:
            rgba(14, 30, 26, 0.9);

        border:
            1px solid #234c3e;

        border-radius:
            18px;

        padding:
            18px;

        margin:
            10px 0;
    }

    input,
    textarea {

        background:
            #0c1815 !important;

        color:
            white !important;
    }

    .thinking {

        display: flex;
        align-items: center;
        gap: 12px;
        padding: 15px;
    }

    .thinking-orb {

        width: 18px;
        height: 18px;

        background: #20d489;

        border-radius: 50%;

        box-shadow:
            0 0 20px #20d489;

        animation:
            thinkingPulse
            1s infinite ease-in-out;
    }

    @keyframes thinkingPulse {

        0%,100% {
            transform: scale(.7);
            opacity: .5;
        }

        50% {
            transform: scale(1.3);
            opacity: 1;
        }
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
# FRIDAY CUSTOM VOICE MODE
# ============================================================

if st.session_state.page_mode == "friday":

    st.markdown(
        """
        <div class="main-title">
            <h1>FRIDAY</h1>
            <p>
                Your intelligent voice companion
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    component_result = voice_assistant_component(
        running=st.session_state.friday_running,
        language="ta-IN",
        audio_b64=st.session_state.friday_audio,
        status=st.session_state.friday_status,
        key="friday_voice_component"
    )


    # ========================================================
    # PROCESS COMPONENT RESULT
    # ========================================================

    if component_result:

        component_running = component_result.get(
            "running"
        )

        if component_running is not None:

            st.session_state.friday_running = (
                bool(component_running)
            )


        user_text = (
            component_result.get(
                "text",
                ""
            ).strip()
        )

        event_id = component_result.get(
            "event_id",
            ""
        )


        if (
            user_text
            and event_id
            and event_id
            != st.session_state.friday_last_event
        ):

            st.session_state.friday_last_event = (
                event_id
            )

            st.session_state.friday_status = (
                "THINKING..."
            )

            st.session_state.friday_audio = ""

            try:

                answer = ask_friday(
                    user_text
                )

                st.session_state.friday_history.append(
                    {
                        "user": user_text,
                        "assistant": answer
                    }
                )

                st.session_state.friday_last_answer = (
                    answer
                )

                st.session_state.friday_status = (
                    "FRIDAY IS SPEAKING..."
                )

                audio = generate_friday_voice(
                    answer
                )

                if audio:

                    st.session_state.friday_audio = (
                        audio
                    )

                else:

                    st.session_state.friday_status = (
                        "READY TO LISTEN"
                    )

                st.rerun()

            except Exception as error:

                st.session_state.friday_status = (
                    "READY TO LISTEN"
                )

                st.error(
                    f"FRIDAY Error: {error}"
                )


    # Optional small status
    st.markdown(
        f"""
        <div style="
            text-align:center;
            color:#8ea89f;
            font-size:13px;
            margin-top:10px;
        ">
            {st.session_state.friday_status}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# CHAT MODE
# ============================================================

elif st.session_state.page_mode == "chat":

    st.markdown(
        """
        <div class="main-title">
            <h1>AI Chat</h1>
            <p>
                Talk naturally • Tamil • English • Tanglish
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    for chat in st.session_state.general_chat_history:

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
                st.session_state.general_chat_history
            )

            with st.chat_message("assistant"):
                type_response(answer)

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


    # ========================================================
    # TRIP DETAILS
    # ========================================================

    st.markdown("### ✈️ Plan Your Trip")

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
            "Days",
            min_value=1,
            value=2
        )

    with c4:

        people = st.number_input(
            "People",
            min_value=1,
            value=2
        )

    with c5:

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

    f1, f2, f3 = st.columns(3)

    with f1:

        fuel_type = st.selectbox(
            "Fuel",
            ["Petrol", "Diesel"]
        )

    with f2:

        mileage = st.number_input(
            "Mileage km/L",
            min_value=1.0,
            value=15.0
        )

    with f3:

        fuel_price = st.number_input(
            "Fuel Price ₹",
            min_value=0.0,
            value=100.0
        )


    if st.button(
        "📍 Calculate Route & Fuel",
        use_container_width=True
    ):

        if not start_location or not destination:

            st.warning(
                "Enter starting location and destination."
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

                    st.session_state.nearby_places = []

                st.success(
                    "Route calculated!"
                )

            except Exception as error:

                st.error(
                    f"Route failed: {error}"
                )


    # ========================================================
    # ROUTE RESULTS
    # ========================================================

    if st.session_state.route:

        route = st.session_state.route

        st.markdown(
            "### 🗺️ Route Result"
        )

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

        r1, r2, r3 = st.columns(3)

        with r1:

            st.metric(
                "One-way",
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

        try:

            show_interactive_map(
                route
            )

        except Exception as error:

            st.warning(
                f"Map unavailable: {error}"
            )


    # ========================================================
    # TOURIST QUESTION
    # ========================================================

    st.markdown("---")
    st.markdown("### 🧠 Ask Tourist AI")

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
                    st.session_state.chat_history
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

        st.markdown("---")
        st.markdown(
            "### 💬 Tourist AI Chat"
        )

        for chat in st.session_state.chat_history:

            with st.chat_message("user"):

                st.markdown(
                    chat["user"]
                )

            with st.chat_message("assistant"):

                st.markdown(
                    chat["assistant"]
                )
