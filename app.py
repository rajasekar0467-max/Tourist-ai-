import streamlit as st
import time
import hashlib
import requests
import base64

from groq import Groq

# ============================================================
# CUSTOM FRIDAY VOICE COMPONENT
# ============================================================

from src.voice_component import voice_assistant_component


# ============================================================
# AI
# ============================================================

from src.ai.groq_service import (
    ask_tourist_ai,
    ask_general_ai
)


# ============================================================
# TRAVEL
# ============================================================

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


# ============================================================
# BUDGET
# ============================================================

from src.budget.budget_calculator import (
    calculate_trip_budget
)


# ============================================================
# CAMERA AI
# ============================================================

from src.camera.camera_service import (
    prepare_image_for_vision
)

from src.camera.vision_service import (
    analyze_prepared_image
)


# ============================================================
# WEATHER
# ============================================================

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

    "camera_analysis": None,

    "last_voice_hash": None,

    "friday_status": "READY TO LISTEN",
    "friday_last_answer": "",
    "friday_audio": "",

    "friday_running": False,
    "friday_last_event": "",

    "voice_speed": 1.0,

    "complete_trip_plan": None,

    "budget_result": None
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
    st.session_state.weather_advice = ""

    st.session_state.nearby_places = []

    st.session_state.camera_analysis = None

    st.session_state.complete_trip_plan = None
    st.session_state.budget_result = None

    st.session_state.last_voice_hash = None

    st.session_state.friday_status = "READY TO LISTEN"
    st.session_state.friday_last_answer = ""
    st.session_state.friday_audio = ""

    st.session_state.friday_running = False
    st.session_state.friday_last_event = ""

    st.rerun()


# ============================================================
# ELEVENLABS FRIDAY VOICE
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

            "Content-Type":
            "application/json",

            "Accept":
            "audio/mpeg"
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

        return base64.b64encode(
            response.content
        ).decode()

    except Exception as error:

        st.session_state.friday_status = (
            "VOICE ERROR"
        )

        st.error(
            f"🔊 FRIDAY voice error: {error}"
        )

        return ""


# ============================================================
# FRIDAY AI
# ============================================================

def ask_friday(user_message):

    friday_prompt = f"""
You are FRIDAY, an advanced intelligent personal AI assistant.

Your personality:
- Warm
- Intelligent
- Friendly
- Calm
- Emotionally aware
- Natural
- Helpful
- Premium AI assistant

Language:
- Understand Tamil
- Understand English
- Understand Tanglish
- Reply naturally in the user's language style.
- Tamil-English mixing is allowed naturally.

Style:
- Speak conversationally.
- Never sound robotic.
- Keep answers concise unless details are needed.
- Be friendly for casual conversations.
- Be intelligent for technical questions.
- Be helpful for travel planning.
- Remember the context of the conversation.

The user said:
{user_message}

Reply naturally as FRIDAY.
"""

    return ask_general_ai(

        friday_prompt,

        voice="FRIDAY",

        language="Tamil + English",

        chat_history=
        st.session_state.friday_history
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

    placeholder.markdown(
        displayed
    )


# ============================================================
# THINKING UI
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
# SAFE BUDGET FUNCTION
# ============================================================

def calculate_budget_safe(
    days,
    people,
    stay_per_day,
    food_per_day,
    activities,
    other
):

    try:

        result = calculate_trip_budget(

            days=days,

            people=people,

            stay_per_day=stay_per_day,

            food_per_day=food_per_day,

            activities=activities,

            other_expenses=other
        )

        return result

    except Exception:

        stay_total = (
            stay_per_day * days
        )

        food_total = (
            food_per_day * days * people
        )

        total = (
            stay_total
            + food_total
            + activities
            + other
        )

        return {

            "stay_total":
            stay_total,

            "food_total":
            food_total,

            "activities":
            activities,

            "other_expenses":
            other,

            "total":
            total
        }


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

#MainMenu,
footer,
header {
    visibility:hidden;
}

.stApp {

    background:
    radial-gradient(
        circle at top,
        #10251f 0%,
        #08110f 45%,
        #050807 100%
    );

    color:white;
}

.block-container {

    max-width:1150px;

    padding-top:1rem;

    padding-bottom:6rem;
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

    color:#f8fafc !important;
}

.main-title {

    text-align:center;

    padding:20px;
}

.main-title h1 {

    color:white !important;

    font-size:42px;

    font-weight:800;
}

.main-title p {

    color:#9ca3af !important;

    font-size:16px;
}


/* BUTTON */

.stButton button {

    background:
    rgba(18,35,30,.92) !important;

    color:white !important;

    border:
    1px solid #245c4a !important;

    border-radius:14px !important;

    min-height:48px;

    font-weight:600;
}

.stButton button:hover {

    border-color:
    #20d489 !important;

    box-shadow:
    0 0 18px
    rgba(32,212,137,.35);
}


/* CARD */

.card {

    background:
    rgba(14,30,26,.92);

    border:
    1px solid #234c3e;

    border-radius:18px;

    padding:18px;

    margin:10px 0;
}


/* INPUT */

input,
textarea {

    background:
    #0c1815 !important;

    color:
    white !important;
}


/* THINKING */

.thinking {

    display:flex;

    align-items:center;

    gap:12px;

    padding:15px;
}

.thinking-orb {

    width:18px;

    height:18px;

    background:#20d489;

    border-radius:50%;

    box-shadow:
    0 0 20px #20d489;

    animation:
    thinkingPulse
    1s infinite ease-in-out;
}

@keyframes thinkingPulse {

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

        running=
        st.session_state.friday_running,

        language="ta-IN",

        audio_b64=
        st.session_state.friday_audio,

        status=
        st.session_state.friday_status,

        key="friday_voice_component"
    )


    # ========================================================
    # PROCESS VOICE RESULT
    # ========================================================

    if component_result:

        component_running = (
            component_result.get(
                "running"
            )
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


        event_id = (
            component_result.get(
                "event_id",
                ""
            )
        )


        if (

            user_text

            and event_id

            and event_id
            !=
            st.session_state.friday_last_event

        ):

            st.session_state.friday_last_event = (
                event_id
            )

            st.session_state.friday_status = (
                "FRIDAY IS THINKING..."
            )

            st.session_state.friday_audio = ""

            try:

                answer = ask_friday(
                    user_text
                )

                st.session_state.friday_history.append(

                    {

                        "user":
                        user_text,

                        "assistant":
                        answer
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


    # ========================================================
    # FRIDAY ANSWER
    # ========================================================

    if st.session_state.friday_last_answer:

        st.markdown("### ✨ FRIDAY")

        st.markdown(
            st.session_state.friday_last_answer
        )


    # ========================================================
    # CLEAR MEMORY
    # ========================================================

    if st.button(
        "🗑️ Clear FRIDAY Memory",
        use_container_width=True
    ):

        st.session_state.friday_history = []

        st.session_state.friday_last_answer = ""

        st.session_state.friday_audio = ""

        st.session_state.friday_status = (
            "READY TO LISTEN"
        )

        st.rerun()


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

            with st.chat_message("assistant"):

                answer = ask_general_ai(

                    user_message,

                    voice="FRIDAY",

                    language="Tamil + English",

                    chat_history=
                    st.session_state.general_chat_history
                )

                type_response(
                    answer
                )


            st.session_state.general_chat_history.append(

                {

                    "user":
                    user_message,

                    "assistant":
                    answer
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

    st.markdown(
        "## ✈️ Plan Your Trip"
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

    st.markdown(
        "## 🚗 Travel & Fuel"
    )


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
            "Fuel Price ₹/L",
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

                    st.session_state.route = (
                        route
                    )

                    st.session_state.fuel = (
                        calculate_fuel_cost(

                            distance_km=float(
                                route.get(
                                    "distance_km",
                                    0
                                )
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
                    f"Route failed: {error}"
                )


    # ========================================================
    # ROUTE RESULT
    # ========================================================

    if st.session_state.route:

        route = (
            st.session_state.route
        )

        st.markdown(
            "## 🗺️ Route Result"
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
                "One-way Distance",
                f"{distance:.1f} km"
            )


        with r2:

            st.metric(
                "Round Trip",
                f"{distance * 2:.1f} km"
            )


        with r3:

            hours = int(
                duration // 60
            )

            minutes = int(
                duration % 60
            )

            st.metric(
                "Driving Time",
                f"{hours}h {minutes}m"
            )


        # MAP

        try:

            show_interactive_map(
                route
            )

        except Exception as error:

            st.warning(
                f"Map unavailable: {error}"
            )


        # FUEL RESULT

        if st.session_state.fuel:

            st.markdown(
                "### ⛽ Fuel Estimate"
            )

            fuel = (
                st.session_state.fuel
            )

            st.json(
                fuel
            )


    # ========================================================
    # WEATHER
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## 🌤️ Destination Weather"
    )


    if st.button(
        "🌦️ Check Weather",
        use_container_width=True
    ):

        try:

            if not destination:

                st.warning(
                    "Enter destination first."
                )

            else:

                with st.spinner(
                    "Checking weather..."
                ):

                    weather = get_weather(
                        destination
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


        except Exception as error:

            st.warning(
                f"Weather unavailable: {error}"
            )


    if st.session_state.weather:

        weather = (
            st.session_state.weather
        )

        st.markdown(
            "### 🌡️ Current Weather"
        )

        st.json(weather)

        if st.session_state.weather_advice:

            st.info(
                st.session_state.weather_advice
            )


    # ========================================================
    # NEARBY PLACES
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## 📍 Nearby Places"
    )


    nearby_category = st.selectbox(

        "Find nearby",

        [
            "Tourist Attractions",
            "Hotels",
            "Restaurants",
            "Hospitals",
            "Petrol Pumps"
        ]
    )


    if st.button(
        "🔎 Find Nearby Places",
        use_container_width=True
    ):

        if not destination:

            st.warning(
                "Enter destination first."
            )

        else:

            try:

                with st.spinner(
                    "Finding nearby places..."
                ):

                    try:

                        places = get_nearby_places(
                            destination,
                            nearby_category
                        )

                    except Exception:

                        places = get_nearby_places(
                            destination
                        )

                    st.session_state.nearby_places = (
                        places or []
                    )


            except Exception as error:

                st.warning(
                    f"Nearby search unavailable: {error}"
                )


    if st.session_state.nearby_places:

        st.markdown(
            "### 🗺️ Places Found"
        )


        for place in st.session_state.nearby_places:

            if isinstance(place, dict):

                name = place.get(
                    "name",
                    "Unknown Place"
                )

                address = place.get(
                    "address",
                    place.get(
                        "vicinity",
                        ""
                    )
                )

            else:

                name = str(place)

                address = ""


            st.markdown(
                f"""
<div class="card">

<h4>📍 {name}</h4>

<p>{address}</p>

</div>
                """,

                unsafe_allow_html=True
            )


            try:

                maps_url = (
                    create_google_maps_place_url(
                        name
                    )
                )

                st.link_button(
                    f"🗺️ Open {name} in Google Maps",
                    maps_url
                )

            except Exception:

                pass


    # ========================================================
    # TRIP BUDGET
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## 💰 Trip Budget Calculator"
    )


    b1, b2 = st.columns(2)


    with b1:

        stay_per_day = st.number_input(

            "🏨 Stay per Day ₹",

            min_value=0.0,

            value=1500.0,

            step=500.0
        )


    with b2:

        food_per_day = st.number_input(

            "🍛 Food per Person / Day ₹",

            min_value=0.0,

            value=500.0,

            step=100.0
        )


    b3, b4 = st.columns(2)


    with b3:

        activities = st.number_input(

            "🎟️ Activities & Entry Fees ₹",

            min_value=0.0,

            value=500.0,

            step=100.0
        )


    with b4:

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

        result = calculate_budget_safe(

            days,

            people,

            stay_per_day,

            food_per_day,

            activities,

            other_expenses
        )

        st.session_state.budget_result = (
            result
        )


    if st.session_state.budget_result:

        result = (
            st.session_state.budget_result
        )

        st.markdown(
            "### 📊 Budget Breakdown"
        )

        st.json(
            result
        )


        total_cost = result.get(
            "total",
            result.get(
                "total_cost",
                0
            )
        )


        if budget > 0:

            remaining = (
                budget - float(total_cost)
            )

            if remaining >= 0:

                st.success(
                    f"🎉 Remaining Budget: ₹{remaining:.2f}"
                )

            else:

                st.error(
                    f"⚠️ Budget exceeds by: ₹{abs(remaining):.2f}"
                )


    # ========================================================
    # CAMERA AI
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## 📸 Camera AI - Analyze Place"
    )


    image_file = st.file_uploader(

        "Upload a travel/place image",

        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )


    if image_file:

        st.image(
            image_file,
            use_container_width=True
        )


        if st.button(
            "🔍 Analyze This Place",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "AI is analyzing the place..."
                ):

                    prepared_image = (
                        prepare_image_for_vision(
                            image_file
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

        st.markdown(
            "### 🤖 AI Place Analysis"
        )

        st.write(
            st.session_state.camera_analysis
        )


    # ========================================================
    # CREATE COMPLETE TRIP PLAN
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## 🗓️ Complete AI Trip Plan"
    )


    if st.button(
        "✨ Create Complete Trip Plan",
        use_container_width=True
    ):

        if not destination:

            st.warning(
                "Enter destination first."
            )

        else:

            route_text = ""

            if st.session_state.route:

                route_text = str(
                    st.session_state.route
                )


            fuel_text = ""

            if st.session_state.fuel:

                fuel_text = str(
                    st.session_state.fuel
                )


            budget_text = ""

            if st.session_state.budget_result:

                budget_text = str(
                    st.session_state.budget_result
                )


            prompt = f"""
Create a complete detailed travel plan.

Starting Location:
{start_location}

Destination:
{destination}

Number of Days:
{days}

Number of People:
{people}

Total Budget:
₹{budget}

Fuel Type:
{fuel_type}

Mileage:
{mileage} km/L

Fuel Price:
₹{fuel_price}

Route Data:
{route_text}

Fuel Estimate:
{fuel_text}

Budget Calculation:
{budget_text}

Create:

1. Day-by-day itinerary
2. Best places to visit
3. Suggested travel route
4. Morning plan
5. Afternoon plan
6. Evening plan
7. Food suggestions
8. Hotel/stay suggestions
9. Budget planning
10. Travel tips
11. What to pack
12. Important safety tips

Reply in Tamil + English naturally.
Make the plan practical and easy to follow.
"""


            try:

                with st.spinner(
                    "FRIDAY is creating your complete trip plan..."
                ):

                    plan = ask_tourist_ai(

                        prompt,

                        voice="FRIDAY",

                        language="Tamil + English",

                        chat_history=
                        st.session_state.chat_history
                    )

                    st.session_state.complete_trip_plan = (
                        plan
                    )


            except Exception as error:

                st.error(
                    f"Trip Plan Error: {error}"
                )


    if st.session_state.complete_trip_plan:

        st.markdown(
            "### 🌍 Your Complete Trip Plan"
        )

        st.markdown(
            st.session_state.complete_trip_plan
        )


    # ========================================================
    # ASK TOURIST AI
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## 🧠 Ask Tourist AI"
    )


    question = st.text_area(

        "Ask anything about your trip",

        placeholder=
        "Ooty-la 2 days trip plan pannu..."
    )


    if st.button(
        "✨ Ask Tourist AI",
        use_container_width=True
    ):

        if question.strip():

            try:

                with st.spinner(
                    "Tourist AI is thinking..."
                ):

                    answer = ask_tourist_ai(

                        question,

                        voice="FRIDAY",

                        language="Tamil + English",

                        chat_history=
                        st.session_state.chat_history
                    )

                    st.session_state.chat_history.append(

                        {

                            "user":
                            question,

                            "assistant":
                            answer
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
            "## 💬 Tourist AI Chat"
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
