import streamlit as st
import textwrap

from src.ai.groq_service import ask_tourist_ai
from src.travel.fuel_calculator import calculate_fuel_cost
from src.maps.distance_service import get_route_distance
from src.budget.budget_calculator import calculate_trip_budget
from src.camera.camera_service import prepare_image_for_vision
from src.camera.vision_service import analyze_prepared_image
from src.maps.map_service import show_interactive_map
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
# NEW CHAT
# ============================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def new_chat():
    """
    Start a completely new Tourist AI chat.
    """

    st.session_state.chat_history = []
    st.session_state.ai_answer = None
    st.session_state.camera_analysis = None

    st.rerun()


# ============================================================
# SESSION STATE
# ============================================================

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


# ============================================================
# VOICE FUNCTION
# ============================================================
def speak_text(text, voice_name):
    """
    Natural browser-based voice.

    JARVIS = Male voice
    EDY    = Female voice
    """

    safe_text = (
        text
        .replace("`", "'")
        .replace("\n", " ")
    )

    if voice_name == "JARVIS":
        voice_type = "male"
        rate = 1.0
        pitch = 0.9
    else:
        voice_type = "female"
        rate = 1.0
        pitch = 1.05

    html = f"""
    <script>
        const text = {safe_text!r};
        const voiceType = "{voice_type}";

        function speak() {{

            const voices =
                window.speechSynthesis.getVoices();

            let selectedVoice = null;

            if (voiceType === "male") {{

                selectedVoice = voices.find(v =>
                    /male|david|mark|daniel|alex|google uk english male/i
                    .test(v.name)
                );

            }} else {{

                selectedVoice = voices.find(v =>
                    /female|samantha|zira|karen|moira|google uk english female/i
                    .test(v.name)
                );
            }}

            if (!selectedVoice) {{
                selectedVoice = voices.find(v =>
                    /en-IN|en-US|en-GB/i
                    .test(v.lang)
                );
            }}

            const utterance =
                new SpeechSynthesisUtterance(text);

            if (selectedVoice) {{
                utterance.voice = selectedVoice;
            }}

            utterance.rate = {rate};
            utterance.pitch = {pitch};
            utterance.volume = 1.0;

            window.speechSynthesis.cancel();

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
                    speak,
                    {{ once: true }}
                );

        }} else {{

            speak();

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
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        .title {
            text-align: center;
            padding-top: 15px;
            padding-bottom: 15px;
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

        .chat-user {
            background: #172033;
            border: 1px solid #273449;
            padding: 18px;
            border-radius: 18px 18px 4px 18px;
            margin: 10px 0;
        }

        .voice-card {
            text-align: center;
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 20px;
        }

        .feature-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 18px;
            padding: 22px;
            min-height: 150px;
            margin-bottom: 18px;
        }

        .feature-icon {
            font-size: 30px;
            margin-bottom: 10px;
        }

        .feature-title {
            font-size: 19px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .feature-text {
            color: #9ca3af;
            font-size: 14px;
            line-height: 1.5;
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
        """
    ),
    unsafe_allow_html=True
)


# ============================================================
# NEW CHAT BUTTON
# ============================================================

new_chat_col1, new_chat_col2, new_chat_col3 = st.columns(
    [1, 2, 1]
)

with new_chat_col2:

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):
        new_chat()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    textwrap.dedent(
        """
        <div class="title">
            <h1>🌍 Tourist AI</h1>
            <p>Your intelligent AI travel companion</p>
        </div>
        """
    ),
    unsafe_allow_html=True
)


# ============================================================
# AI VOICE
# ============================================================

st.markdown("### 🎙️ Choose Your AI")

voice = st.radio(
    "AI Voice",
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


st.markdown(
    textwrap.dedent(
        f"""
        <div class="voice-card">
            <h3>{voice}</h3>
            <span class="small-text">
                {voice_description}
            </span>
        </div>
        """
    ),
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

vehicle_col1, vehicle_col2, vehicle_col3 = st.columns(3)

with vehicle_col1:

    fuel_type = st.selectbox(
        "⛽ Fuel Type",
        ["Petrol", "Diesel"]
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

    if latitude is not None and longitude is not None:

        st.markdown("### 🌦️ Destination Weather")

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

                    st.session_state.weather = weather

                    st.success(
                        "Latest destination weather loaded! 🌦️"
                    )

                except Exception as error:

                    st.error(
                        "Could not get weather."
                    )


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
# BUDGET
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

        st.markdown("### 📊 Budget Summary")

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

        st.markdown("#### Breakdown")

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
                "✅ Great! Your estimated trip is within your budget."
            )

        else:

            st.warning(
                f"⚠️ Your trip is "
                f"₹{abs(budget_result['remaining_budget']):,.0f} "
                f"over the selected budget."
            )

    except Exception:

        st.error(
            "Could not calculate the trip budget."
        )


# ============================================================
# TOURIST AI FEATURES
# ============================================================

st.markdown("---")
st.markdown("### 🚀 Tourist AI Features")

feature1, feature2 = st.columns(2)

with feature1:

    st.markdown(
        textwrap.dedent(
            """
            <div class="feature-card">
                <div class="feature-icon">📍</div>
                <div class="feature-title">
                    Smart Routes
                </div>
                <div class="feature-text">
                    Distance and travel-time estimation
                    for your trip.
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

with feature2:

    st.markdown(
        textwrap.dedent(
            """
            <div class="feature-card">
                <div class="feature-icon">💰</div>
                <div class="feature-title">
                    Budget AI
                </div>
                <div class="feature-text">
                    Build trips around your selected
                    travel budget.
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )


feature3, feature4 = st.columns(2)

with feature3:

    st.markdown(
        textwrap.dedent(
            """
            <div class="feature-card">
                <div class="feature-icon">📷</div>
                <div class="feature-title">
                    Camera AI
                </div>
                <div class="feature-text">
                    Analyze tourist-place photos
                    with AI.
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

with feature4:

    st.markdown(
        textwrap.dedent(
            """
            <div class="feature-card">
                <div class="feature-icon">🎙️</div>
                <div class="feature-title">
                    JARVIS + EDY
                </div>
                <div class="feature-text">
                    Two AI travel personalities for
                    your travel experience.
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )


# ============================================================
# CAMERA AI
# ============================================================

st.markdown("---")

st.markdown("### 📷 Tourist Camera AI")

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
                f"{voice_name} is analyzing the image... 👁️"
            ):

                try:

                    analysis = analyze_prepared_image(
                        image_result,
                        voice=voice_name,
                        language="Tamil + English"
                    )

                    st.session_state.camera_analysis = analysis

                except Exception as error:

                    st.error(
                        "❌ Could not analyze the image."
                    )

    else:

        st.error(
            image_result["message"]
        )


# ============================================================
# CAMERA RESULT
# ============================================================

if st.session_state.camera_analysis:

    st.markdown("### 📍 Place Analysis")

    st.markdown(
        textwrap.dedent(
            f"""
            <div class="chat-ai">
                <b>{voice}</b>
            </div>
            """
        ),
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
# ASK TOURIST AI
# ============================================================

st.markdown("---")

st.markdown("### 🧠 Ask Tourist AI")

user_question = st.text_area(
    "Ask anything about your trip",
    placeholder=(
        "Example: ₹5000 budget-la Ooty 2 days "
        "trip plan pannu..."
    ),
    height=100,
    key="tourist_question"
)


# ============================================================
# WEATHER CONTEXT
# ============================================================

def build_weather_context():

    if not st.session_state.weather:
        return ""

    weather = st.session_state.weather

    description = weather_description(
        weather["weather_code"]
    )

    return f"""
Latest destination weather:

Temperature: {weather['temperature']} °C
Feels like: {weather['feels_like']} °C
Humidity: {weather['humidity']}%
Wind: {weather['wind_speed']} km/h
Condition: {description}

Use this weather information when the user asks
about weather, outdoor activities, sightseeing,
clothing, travel timing, or rain.
"""


# ============================================================
# ASK BUTTON
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

                weather_context = build_weather_context()

                final_question = f"""
You are Tourist AI.

User question:
{user_question}

Trip information:

Starting location:
{start_location or "Not provided"}

Destination:
{destination or "Not provided"}

Number of days:
{days}

Number of people:
{people}

Budget:
₹{budget}

Fuel type:
{fuel_type}

Mileage:
{mileage} km/L

{weather_context}

Answer the user's question clearly.

If the user asks about weather and current
weather data is available above, use that data.

Respond in Tamil + English naturally.
Do not invent live weather information.
"""

                answer = ask_tourist_ai(
                    final_question,
                    voice=voice_name,
                    language="Tamil + English"
                )

                # Save conversation
                st.session_state.chat_history.append(
                    {
                        "user": user_question,
                        "assistant": answer,
                        "voice": voice_name
                    }
                )

                st.session_state.ai_answer = answer

                st.rerun()

            except Exception as error:

                st.error(
                    "❌ Tourist AI Error"
                )

                st.exception(error)


# ============================================================
# CHAT HISTORY
# ============================================================

if st.session_state.chat_history:

    st.markdown("---")
    st.markdown("### 💬 Tourist AI Chat")

    for index, chat in enumerate(
        st.session_state.chat_history
    ):

        # USER MESSAGE
        st.markdown(
            textwrap.dedent(
                f"""
                <div class="chat-user">
                    <b>👤 You</b>
                    <br><br>
                    {chat["user"]}
                </div>
                """
            ),
            unsafe_allow_html=True
        )

        # AI HEADER
        st.markdown(
            textwrap.dedent(
                f"""
                <div class="chat-ai">
                    <b>{voice} {chat["voice"]}</b>
                </div>
                """
            ),
            unsafe_allow_html=True
        )

        # AI ANSWER
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

if st.button(
    "🚀 Create Complete Trip Plan",
    use_container_width=True
):

    if not start_location or not destination:

        st.warning(
            "Please enter starting location "
            "and destination first."
        )

    else:

        with st.spinner(
            f"{voice_name} is creating your complete trip..."
        ):

            try:

                route_text = (
                    "Distance not calculated yet."
                )

                if st.session_state.route:

                    route = st.session_state.route

                    route_text = (
                        f"{route['distance_km']} km one-way, "
                        f"{route['duration_minutes']} minutes"
                    )

                fuel_text = (
                    "Fuel estimate not calculated yet."
                )

                if st.session_state.fuel:

                    fuel = st.session_state.fuel

                    fuel_text = (
                        f"{fuel['fuel_required_litres']} L, "
                        f"₹{fuel['estimated_fuel_cost']}"
                    )

                weather_text = (
                    "Weather not checked yet."
                )

                if st.session_state.weather:

                    weather = st.session_state.weather

                    weather_text = (
                        f"{weather['temperature']} °C, "
                        f"{weather_description(weather['weather_code'])}, "
                        f"humidity {weather['humidity']}%"
                    )

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

Stay per day:
₹{stay_cost_per_day}

Food per day:
₹{food_cost_per_day}

Activities:
₹{activity_cost}

Other expenses:
₹{other_cost}

Weather:
{weather_text}

Create a practical day-by-day travel plan.

Include:

1. 🗺️ Route summary
2. 🌦️ Weather advice
3. 📅 Day-by-day itinerary
4. 🍽️ Food suggestions
5. 🏨 Stay suggestions
6. 🎟️ Activities
7. 💰 Budget summary
8. 🚗 Travel tips
9. ⚠️ Important safety/travel notes

Respond naturally in Tamil + English.

AI personality:
{voice_name}
"""

                answer = ask_tourist_ai(
                    prompt,
                    voice=voice_name,
                    language="Tamil + English"
                )

                st.session_state.chat_history.append(
                    {
                        "user": "🚀 Create Complete Trip Plan",
                        "assistant": answer,
                        "voice": voice_name
                    }
                )

                st.session_state.ai_answer = answer

                st.success(
                    "🎉 Complete trip plan created!"
                )

                st.rerun()

            except Exception as error:

                st.error(
                    "❌ Could not create complete trip plan."
                )

                st.exception(error)
