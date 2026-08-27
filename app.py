import streamlit as st
import json
import hashlib
import time
import base64
import requests
from voice_component import voice_assistant_component
from groq import Groq

from src.ai.groq_service import ask_tourist_ai
from src.travel.fuel_calculator import calculate_fuel_cost
from src.maps.distance_service import get_route_distance
from src.maps.map_service import show_interactive_map
from src.maps.nearby_service import get_nearby_places, create_google_maps_place_url
from src.budget.budget_calculator import calculate_trip_budget
from src.camera.camera_service import prepare_image_for_vision
from src.camera.vision_service import analyze_prepared_image
from src.weather.weather_service import get_weather, weather_description, get_weather_advice


st.set_page_config(page_title="Tourist AI", page_icon="🌍", layout="wide",
                   initial_sidebar_state="collapsed")

DEFAULTS = {
    "page_mode": "chat",
    "chat_history": [],
    "general_chat_history": [],
    "route": None,
    "fuel": None,
    "weather": None,
    "nearby_places": [],
    "camera_analysis": None,
    "last_voice_hash": "",
    "auto_speak_text": "",
    "auto_speak_voice": "JARVIS",
    "voice_running": False,
    "voice_audio_b64": "",
    "voice_event_id": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def get_groq_client():
    key = st.secrets.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not found in Streamlit Secrets.")
    return Groq(api_key=key)


def transcribe_audio(audio_file):
    if audio_file is None:
        return ""
    try:
        data = audio_file.getvalue()
        if not data:
            return ""
        client = get_groq_client()
        response = client.audio.transcriptions.create(
            file=("voice_input.wav", data, "audio/wav"),
            model="whisper-large-v3-turbo",
            response_format="json",
            temperature=0.0,
        )
        return str(getattr(response, "text", "") or "").strip()
    except Exception as e:
        st.error(f"Voice recognition failed: {e}")
        return ""


def ask_general_ai(message, voice_name="JARVIS", history=None):
    if not message.strip():
        return "Solla macha, enna venum?"

    personality = (
        "You are JARVIS: calm, intelligent, precise, helpful and confident."
        if voice_name == "JARVIS"
        else
        "You are EDY: friendly, energetic, casual, helpful and easy to talk to."
    )

    system = f"""
{personality}
You are a general purpose AI assistant, not limited to travel.

Language behavior:
- Understand Tamil script, English, Tanglish and mixed Tamil + English.
- Reply in the same natural style as the user when possible.
- If the user speaks Tanglish, reply naturally in readable Tanglish.
- Do not switch to Indonesian, Malay or another language unless the user asks.
- Avoid unnecessary emojis and decorative symbols.
- Be conversational and practical.
- Do not invent live information or facts.
"""

    messages = [{"role": "system", "content": system}]
    for item in (history or [])[-10:]:
        if item.get("user"):
            messages.append({"role": "user", "content": item["user"]})
        if item.get("assistant"):
            messages.append({"role": "assistant", "content": item["assistant"]})
    messages.append({"role": "user", "content": message})

    response = get_groq_client().chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.7,
        max_completion_tokens=1200,
    )
    return (response.choices[0].message.content or "").strip()


def elevenlabs_tts(text):
    """Generate Tamil/English speech with the user-provided ElevenLabs key/voice."""
    if not text:
        return ""
    api_key = st.secrets.get("ELEVENLABS_API_KEY", "")
    voice_id = st.secrets.get("ELEVENLABS_VOICE_ID", "")
    if not api_key or not voice_id:
        return ""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
    payload = {
        "text": str(text),
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.42, "similarity_boost": 0.78, "style": 0.18, "use_speaker_boost": True},
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=45)
        r.raise_for_status()
        return base64.b64encode(r.content).decode("ascii")
    except Exception as e:
        st.warning(f"ElevenLabs voice unavailable: {e}")
        return ""


def speak_text(text, voice_name):
    """Browser TTS. Uses available Tamil/English device voice; no movie-character imitation."""
    if not text:
        return
    safe = json.dumps(str(text))
    rate = 0.93 if voice_name == "JARVIS" else 1.02
    pitch = 0.92 if voice_name == "JARVIS" else 1.05

    html = f"""
<script>
const text = {safe};
window.speechSynthesis.cancel();

function pickVoice() {{
  const voices = speechSynthesis.getVoices();
  // Prefer Tamil voices, then Indian English.
  const tamil = voices.find(v => /^ta/i.test(v.lang));
  const indian = voices.find(v => /en-IN/i.test(v.lang));
  const english = voices.find(v => /^en/i.test(v.lang));
  return tamil || indian || english || null;
}}

function speakNow() {{
  const u = new SpeechSynthesisUtterance(text);
  const v = pickVoice();
  if (v) u.voice = v;
  u.rate = {rate};
  u.pitch = {pitch};
  u.volume = 1;
  speechSynthesis.speak(u);
}}

if (speechSynthesis.getVoices().length) speakNow();
else speechSynthesis.addEventListener("voiceschanged", speakNow, {{once:true}});
</script>
"""
    st.components.v1.html(html, height=0)


def auto_speak():
    text = st.session_state.get("auto_speak_text", "")
    if text:
        speak_text(text, st.session_state.get("auto_speak_voice", "JARVIS"))
        st.session_state.auto_speak_text = ""


def new_chat():
    for key in ["chat_history", "general_chat_history"]:
        st.session_state[key] = []
    for key in ["route", "fuel", "weather", "nearby_places", "camera_analysis"]:
        st.session_state[key] = [] if key == "nearby_places" else None
    st.session_state.last_voice_hash = ""
    st.rerun()


st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#08111f;color:#f8fafc;}
.block-container {max-width:1200px;padding-top:1rem;padding-bottom:5rem;}
.stMarkdown, .stMarkdown *, p, span, div, label, h1,h2,h3,h4 {color:#f8fafc !important;}
[data-testid="stChatMessage"] {background:#101a2b;border:1px solid #263754;border-radius:18px;margin:8px 0;}
.stTextInput input,.stTextArea textarea,[data-testid="stChatInput"] textarea {
 background:#111b2e !important;color:#fff !important;border-color:#40516c !important;
}
textarea::placeholder,input::placeholder {color:#aab6c8 !important;}
.stButton>button {background:#17243a;color:#fff;border:1px solid #40516c;border-radius:14px;min-height:46px;}
.stButton>button:hover {border-color:#7aa7e8;}
.voice-panel {background:#101a2b;border:1px solid #2e4264;border-radius:18px;padding:16px;margin:10px 0;}
.small-muted {color:#b6c2d4 !important;}
</style>
""", unsafe_allow_html=True)

n1, n2, n3 = st.columns(3)
with n1:
    if st.button("New Chat", use_container_width=True): new_chat()
with n2:
    if st.button("Tourist AI", use_container_width=True):
        st.session_state.page_mode = "tourist"; st.rerun()
with n3:
    if st.button("AI Chat", use_container_width=True):
        st.session_state.page_mode = "chat"; st.rerun()

voice_choice = st.radio("AI personality", ["JARVIS", "EDY"], horizontal=True,
                        label_visibility="collapsed")
voice_name = voice_choice

if st.session_state.page_mode == "chat":
    st.title("AI Chat")
    st.caption("Tamil • English • Tanglish")

    for i, item in enumerate(st.session_state.general_chat_history):
        with st.chat_message("user"):
            st.markdown(item["user"])
        with st.chat_message("assistant"):
            st.markdown(item["assistant"])
            if st.button("Speak", key=f"gs_{i}"):
                speak_text(item["assistant"], item.get("voice", voice_name))

    st.markdown("### Voice Mode")
    voice_running = st.session_state.voice_running
    voice_value = voice_assistant_component(
        key="general_voice_loop",
        running=voice_running,
        language="ta-IN",
        audio_b64=st.session_state.voice_audio_b64,
        status="READY TO LISTEN"
    )
    st.session_state.voice_audio_b64 = ""

    if isinstance(voice_value, dict):
        event_id = voice_value.get("event_id", "")
        spoken = (voice_value.get("text", "") or "").strip()
        if event_id and event_id != st.session_state.voice_event_id:
            st.session_state.voice_event_id = event_id
            st.session_state.voice_running = bool(voice_value.get("running", st.session_state.voice_running))
            if not spoken:
                st.rerun()
            with st.spinner(f"{voice_name} is thinking..."):
                answer = ask_general_ai(spoken, voice_name, st.session_state.general_chat_history)
            st.session_state.general_chat_history.append({"user": spoken, "assistant": answer, "voice": voice_name})
            st.session_state.voice_audio_b64 = elevenlabs_tts(answer)
            st.session_state.voice_running = True
            st.rerun()

    st.markdown("### Text Chat")
    msg = st.chat_input("Message AI...")
    if msg:
        with st.spinner(f"{voice_name} is thinking..."):
            answer = ask_general_ai(msg, voice_name, st.session_state.general_chat_history)
        st.session_state.general_chat_history.append({"user": msg, "assistant": answer, "voice": voice_name})
        st.session_state.auto_speak_text = answer
        st.session_state.auto_speak_voice = voice_name
        st.rerun()

else:
    st.title("Tourist AI")
    st.caption("Plan smarter • Travel better")

    c1, c2 = st.columns(2)
    with c1: start_location = st.text_input("Starting Location", placeholder="Example: Madurai")
    with c2: destination = st.text_input("Destination", placeholder="Example: Ooty")
    c3, c4, c5 = st.columns(3)
    with c3: days = st.number_input("Days", 1, 30, 2)
    with c4: people = st.number_input("People", 1, 50, 2)
    with c5: budget = st.number_input("Total Budget ₹", min_value=0.0, value=5000.0, step=500.0)

    st.subheader("Travel & Fuel")
    f1, f2, f3 = st.columns(3)
    with f1: fuel_type = st.selectbox("Fuel Type", ["Petrol", "Diesel"])
    with f2: mileage = st.number_input("Mileage km/L", min_value=1.0, value=15.0)
    with f3: fuel_price = st.number_input("Fuel Price ₹/L", min_value=0.0, value=100.0)

    if st.button("Calculate Route & Fuel", use_container_width=True):
        if not start_location.strip() or not destination.strip():
            st.warning("Enter starting location and destination.")
        else:
            try:
                with st.spinner("Calculating route..."):
                    route = get_route_distance(start_location, destination)
                    st.session_state.route = route
                    st.session_state.fuel = calculate_fuel_cost(
                        float(route["distance_km"]), float(mileage),
                        float(fuel_price), round_trip=True
                    )
                st.success("Route calculated.")
            except Exception as e:
                st.error(f"Route calculation failed: {e}")

    if st.session_state.route:
        route = st.session_state.route
        st.subheader("Route Result")
        d = float(route.get("distance_km", 0))
        mins = float(route.get("duration_minutes", 0))
        a, b, c = st.columns(3)
        a.metric("One-way Distance", f"{d:.1f} km")
        b.metric("Round Trip", f"{d*2:.1f} km")
        c.metric("Driving Time", f"{int(mins//60)}h {int(mins%60)}m")
        try: show_interactive_map(route)
        except Exception: pass

        st.subheader("Nearby Places")
        p1, p2 = st.columns(2)
        with p1: place_type = st.selectbox("Find Nearby", ["restaurant","hotel","cafe","food"])
        with p2: radius_km = st.selectbox("Radius", [2,5,10,15], index=1)
        if st.button("Find Nearby Places", use_container_width=True):
            lat, lon = route.get("destination_latitude"), route.get("destination_longitude")
            if lat is None or lon is None:
                st.warning("Destination coordinates unavailable.")
            else:
                try:
                    with st.spinner("Searching nearby places..."):
                        st.session_state.nearby_places = get_nearby_places(
                            float(lat), float(lon), place_type, int(radius_km*1000)
                        )
                    if not st.session_state.nearby_places:
                        st.info("No results found. Try a larger radius.")
                except Exception as e:
                    st.error(f"Nearby search failed: {e}")

    for i, place in enumerate(st.session_state.nearby_places):
        name = place.get("name", "Unknown Place")
        st.markdown(f"**{name}** — {place.get('distance_km','?')} km")
        st.caption(place.get("address","Address unavailable"))
        lat, lon = place.get("latitude"), place.get("longitude")
        if lat is not None and lon is not None:
            st.link_button("Open in Maps", create_google_maps_place_url(lat, lon),
                           key=f"place_{i}")

    def build_context():
        return f"""Starting Location: {start_location or 'Not provided'}
Destination: {destination or 'Not provided'}
Days: {days}
People: {people}
Budget: ₹{budget}
Fuel: {fuel_type}, mileage {mileage} km/L, price ₹{fuel_price}/L"""

    st.subheader("Voice Assistant")
    st.caption("One tap → talk → AI replies → automatically listens again. Stop whenever you want.")
    voice_value = voice_assistant_component(
        key="tourist_voice_loop",
        running=st.session_state.voice_running,
        language="ta-IN",
        audio_b64=st.session_state.voice_audio_b64,
        status="READY TO LISTEN"
    )
    st.session_state.voice_audio_b64 = ""

    if isinstance(voice_value, dict):
        event_id = voice_value.get("event_id", "")
        spoken = (voice_value.get("text", "") or "").strip()
        if event_id and event_id != st.session_state.voice_event_id:
            st.session_state.voice_event_id = event_id
            st.session_state.voice_running = bool(voice_value.get("running", st.session_state.voice_running))
            if not spoken:
                st.rerun()
            with st.spinner(f"{voice_name} is planning..."):
                answer = ask_tourist_ai(
                    f"{build_context()}\n\nUser question: {spoken}",
                    voice=voice_name, language="Tamil + English",
                    chat_history=st.session_state.chat_history
                )
            st.session_state.chat_history.append({"user": spoken, "assistant": answer, "voice": voice_name})
            st.session_state.voice_audio_b64 = elevenlabs_tts(answer)
            st.session_state.voice_running = True
            st.rerun()

    st.subheader("Ask Tourist AI")
    question = st.text_area("Your question", placeholder="Example: Ooty-la 2 days budget trip plan pannu")
    if st.button(f"Ask {voice_name}", use_container_width=True):
        if question.strip():
            with st.spinner(f"{voice_name} is thinking..."):
                answer = ask_tourist_ai(
                    f"{build_context()}\n\nUser question: {question}",
                    voice=voice_name, language="Tamil + English",
                    chat_history=st.session_state.chat_history
                )
            st.session_state.chat_history.append({
                "user": question, "assistant": answer, "voice": voice_name
            })
            st.session_state.auto_speak_text = answer
            st.session_state.auto_speak_voice = voice_name
            st.rerun()

    if st.session_state.chat_history:
        st.subheader("Tourist AI Chat")
        for i, item in enumerate(st.session_state.chat_history):
            with st.chat_message("user"): st.markdown(item["user"])
            with st.chat_message("assistant"):
                st.markdown(item["assistant"])
                if st.button("Speak Response", key=f"ts_{i}"):
                    speak_text(item["assistant"], item.get("voice", voice_name))

auto_speak()
