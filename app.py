import streamlit as st
import textwrap
import json
import time
import hashlib

from groq import Groq

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
# PAGE
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
    "nearby_places": [],
    "camera_analysis": None,
    "last_voice_hash": None,
    "auto_speak_text": None,
    "auto_speak_voice": "JARVIS",
    "voice_mode": False,
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
# NEW CHAT
# ============================================================

def new_chat():

    st.session_state.chat_history = []
    st.session_state.general_chat_history = []
    st.session_state.route = None
    st.session_state.fuel = None
    st.session_state.weather = None
    st.session_state.nearby_places = []
    st.session_state.camera_analysis = None
    st.session_state.last_voice_hash = None
    st.session_state.auto_speak_text = None

    st.rerun()


# ============================================================
# VOICE TRANSCRIPTION
# ============================================================

def transcribe_audio(audio_file):

    if audio_file is None:
        return ""

    try:

        audio_bytes = audio_file.getvalue()

        if not audio_bytes:
            return ""

        client = get_groq_client()

        # Streamlit audio input provides browser audio.
        response = client.audio.transcriptions.create(
            file=(
                "voice_input.wav",
                audio_bytes
            ),
            model="whisper-large-v3-turbo",
            response_format="json"
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
            f"🎤 Voice recognition failed: {error}"
        )

        return ""


# ============================================================
# TEXT TO SPEECH
# ============================================================

def speak_text(text, voice_name="JARVIS"):

    if not text:
        return

    if voice_name == "JARVIS":
        rate = 0.90
        pitch = 0.90
    else:
        rate = 1.02
        pitch = 1.03

    safe_text = json.dumps(
        str(text)
    )

    html = f"""
    <script>

    const message = {safe_text};

    function speak() {{

        window.speechSynthesis.cancel();

        const voices =
            window.speechSynthesis.getVoices();

        const utterance =
            new SpeechSynthesisUtterance(
                message
            );

        let selected = null;

        if ("{voice_name}" === "JARVIS") {{

            selected =
                voices.find(v =>
                    /en-IN|ta-IN/i.test(v.lang)
                    && /male|david|mark|daniel|alex/i
                    .test(v.name)
                );

        }} else {{

            selected =
                voices.find(v =>
                    /en-IN|ta-IN/i.test(v.lang)
                );

        }}

        if (!selected) {{

            selected =
                voices.find(v =>
                    /ta-IN/i.test(v.lang)
                )
                ||
                voices.find(v =>
                    /en-IN/i.test(v.lang)
                )
                ||
                voices[0];

        }}

        if (selected) {{
            utterance.voice = selected;
        }}

        utterance.rate = {rate};
        utterance.pitch = {pitch};
        utterance.volume = 1;

        window.speechSynthesis.speak(
            utterance
        );
    }}

    if (
        window.speechSynthesis.getVoices().length
        === 0
    ) {{

        window.speechSynthesis.onvoiceschanged =
            speak;

    }} else {{

        speak();

    }}

    </script>
    """

    st.components.v1.html(
        html,
        height=0
    )


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
# AI TYPING
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

    placeholder.markdown(
        displayed
    )


# ============================================================
# THINKING
# ============================================================

def show_thinking(text):

    st.markdown(
        f"""
        <div class="thinking">
            <div class="blue-orb"></div>
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
        background: #08111f;
        color: #f8fafc;
    }

    .block-container {
        max-width: 1150px;
        padding-top: 1rem;
        padding-bottom: 4rem;
    }

    /* FIX BLACK TEXT */

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

    /* TITLE */

    .main-title {
        text-align: center;
        padding: 20px 10px;
    }

    .main-title h1 {
        color: white !important;
        font-size: 42px;
        margin-bottom: 5px;
    }

    .main-title p {
        color: #aeb8c8 !important;
    }

    /* CARDS */

    .card {
        background: #101a2b;
        border: 1px solid #273a56;
        border-radius: 18px;
        padding: 18px;
        margin: 10px 0;
        color: white !important;
    }

    /* BUTTON */

    .stButton button {
        background: #14233a !important;
        color: white !important;
        border: 1px solid #30486a !important;
        border-radius: 14px !important;
        min-height: 46px;
        font-weight: 600;
    }

    .stButton button:hover {
        border-color: #3b82f6 !important;
    }

    /* INPUT */

    input,
    textarea {
        background: #101a2b !important;
        color: white !important;
    }

    textarea::placeholder,
    input::placeholder {
        color: #94a3b8 !important;
    }

    /* THINKING */

    .thinking {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 15px 5px;
        color: #dbeafe !important;
    }

    .blue-orb {
        width: 18px;
        height: 18px;
        background: #3b82f6;
        border-radius: 50%;
        box-shadow: 0 0 20px #3b82f6;
        animation: orb 1s infinite ease-in-out;
    }

    @keyframes orb {

        0%,100% {
            transform: scale(.7);
            opacity: .5;
        }

        50% {
            transform: scale(1.35);
            opacity: 1;
        }

    }

    /* VOICE */

    .voice-panel {
        background: #0d1929;
        border: 1px solid #284463;
        border-radius: 20px;
        padding: 18px;
        text-align: center;
    }

    [data-testid="stMetricValue"] {
        color: white !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# NAVIGATION
# ============================================================

n1, n2, n3 = st.columns(3)

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
        st.rerun()

with n3:

    if st.button(
        "💬 Chat Mode",
        use_container_width=True
    ):
        st.session_state.page_mode = "chat"
        st.rerun()


# ============================================================
# VOICE SELECT
# ============================================================

st.markdown("---")
st.markdown("### Choose Your AI")

voice_choice = st.radio(
    "AI Voice",
    ["🦾 JARVIS", "🕷️ EDY"],
    horizontal=True,
    label_visibility="collapsed"
)

voice_name = (
    "JARVIS"
    if "JARVIS" in voice_choice
    else "EDY"
)


# ============================================================
# CHAT MODE
# ============================================================

if st.session_state.page_mode == "chat":

    st.markdown(
        """
        <div class="main-title">
            <h1>AI Chat</h1>
            <p>Talk naturally • Tamil • English • Tanglish</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # CHAT HISTORY

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
    # VOICE ASSISTANT
    # ========================================================

    st.markdown("---")

    st.markdown(
        """
        <div class="voice-panel">
            <h3>🎤 Voice Assistant</h3>
            <p>
            Record → Stop → AI replies → AI speaks →
            Ready for your next question
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    voice_audio = st.audio_input(
        "🎤 Speak naturally",
        key="chat_voice"
    )

    if voice_audio is not None:

        audio_bytes = voice_audio.getvalue()

        audio_hash = hashlib.md5(
            audio_bytes
        ).hexdigest()

        audio_hash = (
            "chat_" + audio_hash
        )

        if (
            audio_hash
            != st.session_state.last_voice_hash
        ):

            st.session_state.last_voice_hash = (
                audio_hash
            )

            with st.spinner(
                "🎤 Understanding..."
            ):
                voice_text = transcribe_audio(
                    voice_audio
                )

            if voice_text:

                st.info(
                    f"🎤 You said: **{voice_text}**"
                )

                thinking = st.empty()

                with thinking.container():
                    show_thinking(
                        f"{voice_name} is thinking..."
                    )

                try:

                    answer = ask_general_ai(
                        voice_text,
                        voice=voice_name,
                        language="Tamil + English",
                        chat_history=
                        st.session_state.general_chat_history
                    )

                    thinking.empty()

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

                    thinking.empty()

                    st.error(
                        f"AI Error: {error}"
                    )


    # ========================================================
    # TEXT INPUT
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

        thinking = st.empty()

        with thinking.container():
            show_thinking(
                f"{voice_name} is thinking..."
            )

        try:

            answer = ask_general_ai(
                user_message,
                voice=voice_name,
                language="Tamil + English",
                chat_history=
                st.session_state.general_chat_history
            )

            thinking.empty()

            with st.chat_message(
                "assistant",
                avatar=None
            ):
                type_response(answer)

            st.session_state.general_chat_history.append(
                {
                    "user": user_message,
                    "assistant": answer,
                    "voice": voice_name
                }
            )

        except Exception as error:

            thinking.empty()
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
            <p>Plan • Explore • Discover • Travel Smarter</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # TRIP DETAILS

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
        


    # FUEL

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


    # ROUTE

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
                            distance_km=
                            float(route["distance_km"]),
                            mileage_kmpl=
                            float(mileage),
                            fuel_price=
                            float(fuel_price),
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


    # ROUTE RESULT

    if st.session_state.route:

        route = st.session_state.route

        st.markdown("### 🗺️ Route Result")

        distance = float(
            route.get("distance_km", 0)
        )

        duration = float(
            route.get("duration_minutes", 0)
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
            show_interactive_map(route)
        except Exception as error:
            st.warning(
                f"Map unavailable: {error}"
            )

        maps_url = route.get(
            "google_maps_url"
        )

        if maps_url:

            st.link_button(
                "🗺️ Open in Google Maps",
                maps_url,
                use_container_width=True
            )


    # WEATHER

    if st.session_state.route:

        route = st.session_state.route

        lat = route.get(
            "destination_latitude"
        )

        lon = route.get(
            "destination_longitude"
        )

        st.markdown("### 🌦️ Weather")

        if st.button(
            "🌦️ Check Weather",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Getting weather..."
                ):

                    st.session_state.weather = (
                        get_weather(lat, lon)
                    )

            except Exception as error:
                st.error(
                    f"Weather error: {error}"
                )

    if st.session_state.weather:

        weather = st.session_state.weather

        w1, w2, w3 = st.columns(3)

        with w1:
            st.metric(
                "Temperature",
                f"{weather.get('temperature', '--')} °C"
            )

        with w2:
            st.metric(
                "Humidity",
                f"{weather.get('humidity', '--')}%"
            )

        with w3:
            st.metric(
                "Wind",
                f"{weather.get('wind_speed', '--')} km/h"
            )


    # ========================================================
    # NEARBY PLACES
    # ========================================================

    if st.session_state.route:

        st.markdown("---")
        st.markdown("### 📍 Nearby Places")

        n1, n2 = st.columns(2)

        with n1:

            place_type = st.selectbox(
                "Find",
                [
                    "restaurant",
                    "hotel",
                    "cafe",
                    "food"
                ]
            )

        with n2:

            radius_km = st.selectbox(
                "Radius",
                [2, 5, 10, 15],
                index=1
            )

        if st.button(
            "🔍 Search Nearby",
            use_container_width=True
        ):

            try:

                route = st.session_state.route

                with st.spinner(
                    "Searching places..."
                ):

                    places = get_nearby_places(
                        route[
                            "destination_latitude"
                        ],
                        route[
                            "destination_longitude"
                        ],
                        place_type=place_type,
                        radius=
                        int(radius_km * 1000)
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
                        "No places found. Try bigger radius."
                    )

            except Exception as error:

                st.error(
                    f"Nearby search failed: {error}"
                )

                st.info(
                    "Try again in a few seconds."
                )


    if st.session_state.nearby_places:

        for index, place in enumerate(
            st.session_state.nearby_places
        ):

            name = place.get(
                "name",
                "Unknown"
            )

            st.markdown(
                f"""
                <div class="card">
                    <h4>📍 {name}</h4>
                    <p>
                    📏 {place.get('distance_km')} km away<br>
                    🏷️ {place.get('category')}<br>
                    📌 {place.get('address')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            try:

                maps_url = (
                    create_google_maps_place_url(
                        place["latitude"],
                        place["longitude"],
                        name
                    )
                )

                st.link_button(
                    f"🗺️ Open {name} in Maps",
                    maps_url,
                    key=f"place_{index}",
                    use_container_width=True
                )

            except Exception:
                pass


    # ========================================================
    # TOURIST VOICE ASSISTANT
    # ========================================================

    st.markdown("---")

    st.markdown(
        """
        <div class="voice-panel">
            <h3>🎤 Tourist AI Voice Assistant</h3>
            <p>
            Speak → Stop → Tourist AI replies →
            AI speaks → Ask again
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tourist_audio = st.audio_input(
        "🎤 Ask Tourist AI",
        key="tourist_voice"
    )

    if tourist_audio is not None:

        audio_bytes = tourist_audio.getvalue()

        audio_hash = (
            "tourist_" +
            hashlib.md5(
                audio_bytes
            ).hexdigest()
        )

        if (
            audio_hash
            != st.session_state.last_voice_hash
        ):

            st.session_state.last_voice_hash = (
                audio_hash
            )

            with st.spinner(
                "🎤 Understanding your question..."
            ):

                question = transcribe_audio(
                    tourist_audio
                )

            if question:

                st.info(
                    f"🎤 You said: **{question}**"
                )

                thinking = st.empty()

                with thinking.container():

                    show_thinking(
                        f"{voice_name} is planning..."
                    )

                context = f"""
Starting location: {start_location}
Destination: {destination}
Days: {days}
People: {people}
Budget: ₹{budget}
"""

                try:

                    answer = ask_tourist_ai(
                        f"""
Trip Context:
{context}

User Question:
{question}

Answer naturally in Tamil + English.
""",
                        voice=voice_name,
                        language="Tamil + English",
                        chat_history=
                        st.session_state.chat_history
                    )

                    thinking.empty()

                    st.session_state.chat_history.append(
                        {
                            "user": question,
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

                    thinking.empty()

                    st.error(
                        f"AI Error: {error}"
                    )


    # ========================================================
    # TEXT TOURIST AI
    # ========================================================

    st.markdown("---")
    st.markdown("### 🧠 Ask Tourist AI")

    question = st.text_area(
        "Ask about your trip",
        placeholder=
        "Ooty-la 2 days trip plan pannu..."
    )

    if st.button(
        f"✨ Ask {voice_name}",
        use_container_width=True
    ):

        if question.strip():

            thinking = st.empty()

            with thinking.container():
                show_thinking(
                    f"{voice_name} is thinking..."
                )

            try:

                answer = ask_tourist_ai(
                    question,
                    voice=voice_name,
                    language="Tamil + English",
                    chat_history=
                    st.session_state.chat_history
                )

                thinking.empty()

                st.session_state.chat_history.append(
                    {
                        "user": question,
                        "assistant": answer,
                        "voice": voice_name
                    }
                )

                st.rerun()

            except Exception as error:

                thinking.empty()

                st.error(
                    f"AI Error: {error}"
                )

        else:
            st.warning(
                "Ask something first."
            )


    # CHAT HISTORY

    if st.session_state.chat_history:

        st.markdown("---")
        st.markdown("### 💬 Tourist AI Chat")

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


# ============================================================
# AUTO SPEAK MUST BE LAST
# ============================================================

run_auto_speak()
