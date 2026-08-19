import streamlit as st
from groq import Groq


MODEL_NAME = "openai/gpt-oss-20b"


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


def ask_tourist_ai(
    user_message: str,
    voice: str = "JARVIS",
    language: str = "Tamil + English"
) -> str:

    client = get_groq_client()

    if voice == "JARVIS":
        personality = """
You are JARVIS, a calm, intelligent and professional
travel AI assistant.
"""
    else:
        personality = """
You are EDY, a friendly, energetic and helpful
travel AI assistant.
"""

    system_prompt = f"""
{personality}

You are Tourist AI, an intelligent travel companion.

Help users with:
- Trip planning
- Tourist places
- Budget planning
- Distance and travel calculations
- Fuel cost estimates
- Food and accommodation suggestions
- Travel tips
- Itinerary planning

Language preference: {language}

Reply naturally using Tamil + English when requested.

Do not invent live prices, live weather,
or live map information.

Clearly identify estimates.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.7,
        max_completion_tokens=1000
    )

    return response.choices[0].message.content
