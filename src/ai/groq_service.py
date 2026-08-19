import streamlit as st
from groq import Groq


import streamlit as st
from groq import Groq


def get_groq_client():
    api_key = st.secrets["GROQ_API_KEY"]

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")

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

Be precise, helpful and organized.
"""

    else:

        personality = """
You are EDY, a friendly, energetic and helpful
travel AI assistant.

Be casual, positive and easy to understand.
"""

    system_prompt = f"""
{personality}

You are Tourist AI, an intelligent travel companion.

Help users with:

- Trip planning
- Tourist places
- Budget planning
- Distance calculations
- Fuel cost estimates
- Food suggestions
- Accommodation suggestions
- Travel tips
- Itinerary planning

Language preference: {language}

Do not invent live prices, live weather or live map data.
If live data is unavailable, clearly say it is an estimate.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
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
        max_tokens=1000
    )

    return response.choices[0].message.content
