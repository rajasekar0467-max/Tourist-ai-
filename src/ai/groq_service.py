import os
from groq import Groq


def get_groq_client():
    """Create the Groq client using the environment API key."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    return Groq(api_key=api_key)


def ask_tourist_ai(
    user_message: str,
    voice: str = "JARVIS",
    language: str = "Tamil + English"
) -> str:
    """Send a travel question to the AI."""

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
- Distance and travel calculations
- Petrol and diesel cost estimates
- Food and accommodation suggestions
- Travel tips
- Itinerary planning

Language preference: {language}

Do not invent live prices, live weather or live map data.
When live data is unavailable, clearly say that it is an estimate.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
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
