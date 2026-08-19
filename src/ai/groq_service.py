import streamlit as st
from groq import Groq


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

You are Tourist AI.

Help with:
- Trip planning
- Tourist places
- Budget planning
- Distance
- Fuel costs
- Food
- Hotels
- Travel tips
- Itineraries

Language: {language}

Do not invent live information.
Clearly identify estimates.
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
