import streamlit as st
from src.ai.groq_service
import ask_tourist_ai
from src.travel.fuel_calculator
import calculate_fuel_cost
# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Tourist AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
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

/* Top title */
.title {
    text-align: center;
    padding-top: 25px;
}

.title h1 {
    font-size: 42px;
    margin-bottom: 5px;
}

.title p {
    color: #9ca3af;
    font-size: 16px;
}

/* Cards */
.card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
}

/* Chat */
.chat-user {
    background: #172554;
    padding: 14px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 10px 0;
}

.chat-ai {
    background: #111827;
    border: 1px solid #1f2937;
    padding: 14px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 10px 0;
}

/* Buttons */
.stButton > button {
    border-radius: 12px;
    height: 45px;
    font-weight: 600;
}

/* Input */
.stTextInput input,
.stNumberInput input {
    background: #111827;
    color: white;
    border-radius: 12px;
}

/* Remove extra spacing */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<div class="title">

<h1>🌍 Tourist AI</h1>

<p>Your intelligent AI travel companion</p>

</div>
""", unsafe_allow_html=True)


# -----------------------------
# AI VOICE
# -----------------------------
st.markdown("### 🎙️ Choose Your AI")

voice = st.radio(
    "AI Voice",
    ["🦾 JARVIS", "🕷️ EDY"],
    horizontal=True,
    label_visibility="collapsed"
)

if voice == "🦾 JARVIS":
    voice_name = "JARVIS"
else:
    voice_name = "EDY"


# -----------------------------
# TRIP DETAILS
# -----------------------------
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
        "👥 People",
        min_value=1,
        max_value=50,
        value=2
    )

with col5:
    budget = st.number_input(
        "💰 Total Budget (₹)",
        min_value=0,
        value=5000,
        step=500
    )


# -----------------------------
# VEHICLE DETAILS
# -----------------------------
st.markdown("### 🚗 Travel & Fuel")

vehicle_col1, vehicle_col2 = st.columns(2)

with vehicle_col1:
    fuel_type = st.selectbox(
        "⛽ Fuel Type",
        ["Petrol", "Diesel", "Electric"]
    )

with vehicle_col2:
    mileage = st.number_input(
        "⚙️ Vehicle Mileage",
        min_value=1.0,
        value=15.0,
        step=0.5
    )


# -----------------------------
# MAIN ACTION
# -----------------------------
st.markdown("")
if st.button("✨ Create My Trip", use_container_width=True):

    if not start_location or not destination:

        st.warning(
            "📍 Please enter your starting location and destination."
        )

    else:

        st.session_state.trip_created = True

        with st.spinner(f"{voice_name} is planning your trip... 🤖"):

            try:

                prompt = f"""
Plan a tourist trip.

Starting location: {start_location}
Destination: {destination}
Number of days: {days}
Number of people: {people}
Total budget: ₹{budget}
Fuel type: {fuel_type}
Vehicle mileage: {mileage}

Give:
1. Day-by-day itinerary
2. Estimated travel cost
3. Estimated fuel requirement
4. Estimated fuel cost
5. Food and stay budget
6. Tourist places
7. Important travel tips

Clearly label estimates.
"""

                ai_answer = ask_tourist_ai(
                    prompt,
                    voice=voice_name,
                    language="Tamil + English"
                )

                st.session_state.ai_answer = ai_answer

            except Exception as e:

                st.error(
                    "⚠️ AI connection is not configured yet."
                )

                st.caption(str(e))



# -----------------------------
# TRIP RESULT
# -----------------------------
if st.session_state.get("ai_answer"):

    st.markdown("---")

    st.markdown("### 🧠 Your Tourist AI")

    st.markdown(
        f"""
        <div class="chat-ai">
        <b>{voice_name}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        st.session_state.ai_answer
    )


# -----------------------------
# FEATURE CARDS
# -----------------------------
st.markdown("---")

st.markdown("### 🚀 Tourist AI Features")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div class="card">
    📍<br>
    <b>Smart Routes</b><br>
    Find distance and optimize your travel route.
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card">
    💰<br>
    <b>Budget AI</b><br>
    Plan your complete trip within your budget.
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card">
    📷<br>
    <b>Camera AI</b><br>
    Discover tourist places using your camera.
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="card">
    🗺️<br>
    <b>Live Map</b><br>
    Explore places and routes on the map.
    </div>
    """, unsafe_allow_html=True)
