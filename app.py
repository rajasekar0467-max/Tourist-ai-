
import streamlit as st
import textwrap
import json
import time
import hashlib

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
    "last_voice_hash": None,
    "voice_processing": False
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

    return Groq(
        api_key=api_key
    )


# ============================================================
# GENERAL AI
# ============================================================

def ask_general_ai(
    user_message,
    voice_name="JARVIS",
    history=None
):

    if not user_message.strip():

        return "Enna venum nu sollu 🙂"

    client = get_groq_client()

    if voice_name == "JARVIS":

        personality = """
You are JARVIS, an intelligent AI assistant.

Your personality:
- Calm
- Intelligent
- Clear
- Professional
- Helpful
- Friendly

For Tamil/Tanglish conversations:
Speak naturally like a smart Tamil friend.
Use simple conversational Tanglish when appropriate.

Examples:
"Sollu da, enna venum?"
"Seri, naan help pannuren."
"Idhu easy da, ippadi pannalaam."

Do not overuse these phrases.
Do not imitate any actor or movie character.
"""

    else:

        personality = """
You are EDY, a friendly AI assistant.

Your personality:
- Friendly
- Energetic
- Casual
- Helpful
- Smart

For Tamil/Tanglish conversations:
Speak naturally and casually.

Examples:
"Hey sollu da!"
"Seri macha, naan help pannuren."
"Idhu simple dhaan."

Do not overuse these phrases.
Do not imitate any actor or movie character.
"""

    system_prompt = f"""
{personality}

You are a general purpose AI assistant.

You can help with:

- Study
- Coding
- Programming
- Technology
- General knowledge
- Ideas
- Writing
- Travel
- Daily questions
- Problem solving

Language rules:

- Understand Tamil script.
- Understand Tamil written in English letters.
- Understand English.
- Understand Tanglish.
- Reply in the user's natural language style.
- Keep answers clear and useful.
- Do not invent facts.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if history:

        for chat in history[-10:]:

            user_text = chat.get(
                "user",
                ""
            )

            assistant_text = chat.get(
                "assistant",
                ""
            )

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
# VOICE TO TEXT
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
# TEXT TO SPEECH
# ============================================================

def speak_text(text, voice_name):

    if not text:
        return

    clean_text = str(text)

    safe_text = json.dumps(
        clean_text
    )

    if voice_name == "JARVIS":

        rate = 0.92
        pitch = 0.88

    else:

        rate = 1.02
        pitch = 1.04

    html = f"""
    <script>

    const text = {safe_text};

    window.speechSynthesis.cancel();

    function speakNow() {{

        const utterance =
            new SpeechSynthesisUtterance(text);

        const voices =
            window.speechSynthesis.getVoices();

        let selectedVoice = null;

        // Prefer Tamil voice
        selectedVoice = voices.find(
            voice =>
            voice.lang &&
            voice.lang.toLowerCase().startsWith("ta")
        );

        // Indian English fallback
        if (!selectedVoice) {{

            selectedVoice = voices.find(
                voice =>
                voice.lang &&
                voice.lang.toLowerCase().includes("en-in")
            );

        }}

        // English fallback
        if (!selectedVoice) {{

            selectedVoice = voices.find(
                voice =>
                voice.lang &&
                (
                    voice.lang.toLowerCase().includes("en-us")
                    ||
                    voice.lang.toLowerCase().includes("en-gb")
                )
            );

        }}

        if (!selectedVoice && voices.length > 0) {{

            selectedVoice = voices[0];

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

        window.speechSynthesis.onvoiceschanged =
            speakNow;

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
# STOP VOICE
# ============================================================

def stop_voice():

    html = """
    <script>
    window.speechSynthesis.cancel();
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
# CSS
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
            background: #08111f !important;
            color: #f8fafc !important;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 1rem;
            padding-bottom: 5rem;
        }

        /* FIX TEXT */

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
        .stMarkdown h6,
        p,
        span,
        label {
            color: #f8fafc !important;
        }

        /* TITLE */

        .title {
            text-align: center;
            padding: 20px 10px;
        }

        .title h1 {
            font-size: 46px;
            color: white !important;
            margin-bottom: 5px;
        }

        .title p {
            color: #aeb8c8 !important;
        }

        /* CARD */

        .card {
            background: #111b2e;
            border: 1px solid #2a3850;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 15px;
        }

        /* BUTTON */

        .stButton > button {

            border-radius: 14px;
            min-height: 46px;
            font-weight: 600;

            color: #ffffff !important;

            background: #17243a;

            border: 1px solid #314564;
        }

        /* INPUT */

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

        /* CHAT */

        [data-testid="stChatMessage"] {

            background: transparent !important;

        }

        /* THINKING */

        .thinking-area {

            display: flex;

            align-items: center;

            gap: 12px;

            padding: 15px 5px;

        }

        .blue-ball {

            width: 17px;

            height: 17px;

            background: #3b82f6;

            border-radius: 50%;

            animation:
                pulseBall 1s infinite ease-in-out;

            box-shadow:
                0 0 18px #3b82f6;

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
                transform: scale(1.3);
                opacity: 1;
            }

            100% {
                transform: scale(0.7);
                opacity: 0.4;
            }

        }

        /* METRICS */

        [data-testid="stMetricValue"] {
            color: white !important;
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

nav1, nav2, nav3 = st.columns(3)

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
# VOICE SELECTOR
# ============================================================

st.markdown("---")

voice = st.radio(

    "Choose AI",

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

st.caption(
    f"🤖 {voice_name} — {voice_description}"
)


# ============================================================
# STOP VOICE BUTTON
# ============================================================

if st.button(
    "⏹️ Stop Voice",
    use_container_width=False
):

    stop_voice()


# ============================================================
# CHAT MODE
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
    st.markdown("### 🎤 Voice Assistant")

    st.caption(
        "Record → Speak → Stop → AI replies automatically"
    )

    voice_audio = st.audio_input(
        "🎤 Speak Tamil, English or Tanglish",
        key="general_voice_input"
    )

    if voice_audio is not None:

        audio_bytes = voice_audio.getvalue()

        audio_hash = hashlib.md5(
            audio_bytes
        ).hexdigest()

        if (
            audio_hash
            != st.session_state.last_voice_hash
        ):

            st.session_state.last_voice_hash = audio_hash

            with st.spinner(
                "🎤 Understanding your voice..."
            ):

                voice_text = transcribe_audio(
                    voice_audio
                )

            if voice_text:

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
    # TEXT INPUT
    # ========================================================

    user_message = st.chat_input(
        "Message AI..."
    )

    if user_message:

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

                    time.sleep(0.002)

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
    # TRIP DETAILS
    # ========================================================

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
                    "Route calculated successfully!"
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

        hours = int(duration // 60)
        minutes = int(duration % 60)

        st.markdown("### 🗺️ Route Result")

        r1, r2, r3 = st.columns(3)

        with r1:

            st.metric(
                "📍 One-way",
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

        try:

            show_interactive_map(
                route
            )

        except Exception as error:

            st.warning(
                f"Map unavailable: {error}"
            )

        google_maps_url = route.get(
            "google_maps_url"
        )

        if google_maps_url:

            st.link_button(
                "🗺️ Open in Google Maps",
                google_maps_url,
                use_container_width=True
            )


    # ========================================================
    # NEARBY PLACES
    # ========================================================

    if st.session_state.route:

        st.markdown("---")
        st.markdown(
            "### 📍 Discover Nearby Places"
        )

        n1, n2 = st.columns(2)

        with n1:

            place_type = st.selectbox(
                "Find Nearby",
                [
                    "restaurant",
                    "hotel",
                    "cafe",
                    "food"
                ]
            )

        with n2:

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
                        "Searching restaurants and places..."
                    ):

                        places = get_nearby_places(

                            latitude=float(latitude),

                            longitude=float(longitude),

                            place_type=place_type,

                            radius=int(
                                radius_km * 1000
                            ),

                            limit=12
                        )

                        st.session_state.nearby_places = (
                            places
                        )

                    if places:

                        st.success(
                            f"✅ {len(places)} places found!"
                        )

                    else:

                        st.info(
                            "No places found. Try a larger radius."
                        )

            except Exception as error:

                error_text = str(error)

                st.error(
                    "Nearby search is temporarily unavailable."
                )

                st.caption(
                    f"Server message: {error_text}"
                )

                st.info(
                    "Try again after a few seconds. "
                    "The backup nearby servers are also checked automatically."
                )


    # ========================================================
    # NEARBY RESULTS
    # ========================================================

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
                        📏 {distance_km} km away<br>
                        🏷️ {category}<br>
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

                maps_url = (
                    create_google_maps_place_url(
                        latitude,
                        longitude,
                        name
                    )
                )

                st.link_button(
                    f"🗺️ Open {name} in Google Maps",
                    maps_url,
                    key=f"place_map_{index}",
                    use_container_width=True
                )


    # ========================================================
    # BUILD AI CONTEXT
    # ========================================================

    def build_ai_context():

        context = f"""
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

Distance:
{route.get("distance_km")} km

Driving Time:
{route.get("duration_minutes")} minutes
"""

        return context


    # ========================================================
    # TOURIST VOICE INPUT
    # ========================================================

    st.markdown("---")
    st.markdown(
        "### 🎤 Tourist AI Voice Assistant"
    )

    st.caption(
        "Record → Speak → Stop → AI replies automatically"
    )

    tourist_voice_audio = st.audio_input(
        "🎤 Ask Tourist AI",
        key="tourist_voice_input"
    )

    if tourist_voice_audio is not None:

        audio_bytes = (
            tourist_voice_audio.getvalue()
        )

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
                "🎤 Understanding your voice..."
            ):

                voice_question = transcribe_audio(
                    tourist_voice_audio
                )

            if voice_question:

                thinking_box = st.empty()

                with thinking_box.container():

                    show_thinking(
                        f"{voice_name} is thinking..."
                    )

                try:

                    context = build_ai_context()

                    final_question = f"""
{context}

User Question:
{voice_question}

Answer naturally in Tamil + English.
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
    st.markdown("### 🧠 Ask Tourist AI")

    user_question = st.text_area(

        "Ask about your trip",

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
                "Please type or speak a question."
            )

        else:

            thinking_box = st.empty()

            with thinking_box.container():

                show_thinking(
                    f"{voice_name} is thinking..."
                )

            try:

                context = build_ai_context()

                final_question = f"""
{context}

User Question:
{user_question}

Answer naturally in Tamil + English.
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

                thinking_box.empty()

                st.error(
                    f"Tourist AI Error: {error}"
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
    # FOOTER
    # ========================================================

    st.markdown("---")

    st.caption(
        "🌍 Tourist AI • Plan smarter • Travel better"
    )


# ============================================================
# RUN AUTO SPEECH
# ============================================================

run_auto_speak()
