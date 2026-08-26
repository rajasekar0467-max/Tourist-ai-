import streamlit as st
import json
import time
import hashlib
import requests
import base64

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

    "friday_status": "READY",
    "friday_last_answer": "",
    "friday_audio": None,

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

    st.session_state.last_voice_hash = None

    st.session_state.friday_status = "READY"
    st.session_state.friday_last_answer = ""
    st.session_state.friday_audio = None

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

        response = client.audio.transcriptions.create(
            file=(
                "friday_voice.wav",
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
# ELEVENLABS PREMIUM TTS
# ============================================================

def generate_friday_voice(
    text,
    speed=1.0
):

    if not text:
        return None

    try:

        api_key, voice_id = (
            get_elevenlabs_config()
        )

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

            "model_id":
            "eleven_multilingual_v2",

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

            raise Exception(
                response.text
            )

        audio_base64 = base64.b64encode(
            response.content
        ).decode()

        return audio_base64

    except Exception as error:

        st.error(
            f"🔊 FRIDAY voice error: {error}"
        )

        return None


# ============================================================
# PLAY FRIDAY AUDIO
# ============================================================

def play_friday_audio(
    audio_base64,
    speed=1.0
):

    if not audio_base64:
        return

    speed = max(
        0.75,
        min(float(speed), 1.25)
    )

    html = f"""
    <audio
        id="friday-audio"
        autoplay
        style="display:none"
    >
        <source
            src="data:audio/mpeg;base64,{audio_base64}"
            type="audio/mpeg"
        >
    </audio>

    <script>

    const audio =
        document.getElementById(
            "friday-audio"
        );

    audio.playbackRate =
        {speed};

    audio.play().catch(
        error => console.log(error)
    );

    </script>
    """

    st.components.v1.html(
        html,
        height=0
    )


# ============================================================
# FRIDAY AI
# ============================================================

def ask_friday(
    user_message
):

    friday_prompt = f"""
You are FRIDAY, a premium personal AI assistant.

Personality:
- Warm
- Intelligent
- Friendly
- Emotionally aware
- Calm
- Natural
- Helpful

Language rules:
- Understand Tamil
- Understand English
- Understand Tanglish
- Reply naturally in the language style used by the user.
- Tamil-English mixing is allowed when natural.

Conversation style:
- Sound human and conversational.
- Show appropriate warmth and emotion.
- Do not sound robotic.
- Do not use overly long replies unless necessary.
- For casual conversation, respond naturally like a helpful AI companion.
- For serious questions, be calm and supportive.

The user said:
{user_message}

Reply as FRIDAY.
"""

    answer = ask_general_ai(
        friday_prompt,
        voice="FRIDAY",
        language="Tamil + English",
        chat_history=
        st.session_state.friday_history
    )

    return answer


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

    /* TITLE */

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

    /* BUTTON */

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

    /* CARDS */

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

    /* INPUT */

    input,
    textarea {

        background:
            #0c1815 !important;

        color:
            white !important;

    }

    /* FRIDAY MAIN */

    .friday-container {

        min-height:
            520px;

        display:
            flex;

        flex-direction:
            column;

        align-items:
            center;

        justify-content:
            center;

        text-align:
            center;

    }

    .friday-name {

        font-size:
            46px;

        font-weight:
            700;

        letter-spacing:
            7px;

        margin-bottom:
            8px;

        color:
            #f8fafc !important;

    }

    .friday-subtitle {

        color:
            #8ea89f !important;

        margin-bottom:
            45px;

    }

    /* GREEN ORB */

    .friday-orb {

        width:
            210px;

        height:
            210px;

        border-radius:
            50%;

        background:
            radial-gradient(
                circle at 35% 30%,
                #a7ffd7,
                #25c981 35%,
                #0d8052 60%,
                #043a27
            );

        box-shadow:

            0 0 30px
            rgba(39, 255, 157, 0.8),

            0 0 70px
            rgba(32, 212, 137, 0.5),

            0 0 130px
            rgba(18, 255, 137, 0.25);

        animation:
            fridayPulse
            2.5s
            infinite
            ease-in-out;

        margin-bottom:
            40px;

    }

    @keyframes fridayPulse {

        0% {

            transform:
                scale(0.95);

            box-shadow:
                0 0 25px
                rgba(39,255,157,.5);

        }

        50% {

            transform:
                scale(1.08);

            box-shadow:

                0 0 55px
                rgba(39,255,157,.9),

                0 0 120px
                rgba(39,255,157,.45);

        }

        100% {

            transform:
                scale(.95);

        }

    }

    .friday-status {

        color:
            #35e896 !important;

        font-size:
            15px;

        letter-spacing:
            2px;

        font-weight:
            700;

    }

    /* THINKING */

    .thinking {

        display:
            flex;

        align-items:
            center;

        gap:
            12px;

        padding:
            15px;

    }

    .blue-orb {

        width:
            18px;

        height:
            18px;

        background:
            #20d489;

        border-radius:
            50%;

        box-shadow:
            0 0 20px #20d489;

        animation:
            orb 1s infinite ease-in-out;

    }

    @keyframes orb {

        0%,100% {
            transform:scale(.7);
            opacity:.5;
        }

        50% {
            transform:scale(1.3);
            opacity:1;
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
        st.rerun()


with n3:

    if st.button(
        "💬 Chat Mode",
        use_container_width=True
    ):
        st.session_state.page_mode = "chat"
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

if st.session_state.page_mode == "friday":

    st.markdown(
        """
        <div class="friday-container">

            <div class="friday-name">
                FRIDAY
            </div>

            <div class="friday-subtitle">
                Your intelligent travel companion
            </div>

            <div class="friday-orb"></div>

            <div class="friday-status">
                READY TO LISTEN
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:

        speed = st.slider(
            "🎚️ Voice Speed",
            min_value=0.8,
            max_value=1.2,
            value=float(
                st.session_state.voice_speed
            ),
            step=0.05
        )

        st.session_state.voice_speed = speed

    with c2:

        if st.button(
            "🗑️ Clear FRIDAY Memory",
            use_container_width=True
        ):

            st.session_state.friday_history = []
            st.session_state.friday_last_answer = ""

            st.rerun()


    # VOICE INPUT

    st.markdown("### 🎤 Talk to FRIDAY")

    friday_audio = st.audio_input(
        "Press record and speak",
        key="friday_voice_input"
    )


    if friday_audio is not None:

        audio_bytes = friday_audio.getvalue()

        audio_hash = (
            "friday_" +
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

            st.session_state.friday_status = (
                "LISTENING"
            )

            with st.spinner(
                "🎤 FRIDAY is listening..."
            ):

                user_text = (
                    transcribe_audio(
                        friday_audio
                    )
                )

            if user_text:

                st.markdown(
                    f"### You\n{user_text}"
                )

                st.session_state.friday_status = (
                    "THINKING"
                )

                thinking = st.empty()

                with thinking.container():

                    show_thinking(
                        "FRIDAY is thinking..."
                    )

                try:

                    answer = ask_friday(
                        user_text
                    )

                    thinking.empty()

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
                        "SPEAKING"
                    )

                    st.markdown(
                        "### ✨ FRIDAY"
                    )

                    type_response(
                        answer
                    )

                    with st.spinner(
                        "🔊 FRIDAY is speaking..."
                    ):

                        audio = (
                            generate_friday_voice(
                                answer,
                                speed
                            )
                        )

                    if audio:

                        st.session_state.friday_audio = (
                            audio
                        )

                        play_friday_audio(
                            audio,
                            speed
                        )

                        st.audio(
                            base64.b64decode(
                                audio
                            ),
                            format="audio/mpeg"
                        )

                    st.session_state.friday_status = (
                        "READY"
                    )

                except Exception as error:

                    thinking.empty()

                    st.session_state.friday_status = (
                        "READY"
                    )

                    st.error(
                        f"FRIDAY Error: {error}"
                    )


    # TEXT INPUT

    st.markdown("---")

    friday_text = st.chat_input(
        "Message FRIDAY..."
    )

    if friday_text:

        with st.spinner(
            "FRIDAY is thinking..."
        ):

            try:

                answer = ask_friday(
                    friday_text
                )

                st.session_state.friday_history.append(
                    {
                        "user": friday_text,
                        "assistant": answer
                    }
                )

                st.markdown(
                    f"### You\n{friday_text}"
                )

                st.markdown(
                    "### ✨ FRIDAY"
                )

                type_response(
                    answer
                )

                audio = (
                    generate_friday_voice(
                        answer,
                        st.session_state.voice_speed
                    )
                )

                if audio:

                    play_friday_audio(
                        audio,
                        st.session_state.voice_speed
                    )

                    st.audio(
                        base64.b64decode(
                            audio
                        ),
                        format="audio/mpeg"
                    )

            except Exception as error:

                st.error(
                    f"FRIDAY Error: {error}"
                )


    # HISTORY

    if st.session_state.friday_history:

        st.markdown("---")
        st.markdown("### 💬 Conversation")

        for chat in reversed(
            st.session_state.friday_history[-10:]
        ):

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    chat["user"]
                )

            with st.chat_message(
                "assistant"
            ):

                st.markdown(
                    chat["assistant"]
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
            st.markdown(chat["user"])

        with st.chat_message("assistant"):
            st.markdown(chat["assistant"])


    user_message = st.chat_input(
        "Message AI..."
    )

    if user_message:

        with st.chat_message("user"):
            st.markdown(user_message)

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


    # ROUTE RESULTS

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


    # TOURIST QUESTION

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
