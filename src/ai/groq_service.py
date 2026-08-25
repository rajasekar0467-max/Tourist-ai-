import streamlit as st
from groq import Groq


MODEL_NAME = "openai/gpt-oss-20b"


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
# SPELLING CORRECTION
# ============================================================

def correct_spelling(
    text: str,
    language: str = "Tamil + English"
) -> str:
    """
    Correct obvious spelling mistakes while
    preserving the user's original meaning.

    Useful for Tamil written in English letters,
    English, and mixed Tamil + English text.
    """

    if not text or not text.strip():

        return text

    client = get_groq_client()

    prompt = f"""
Correct only obvious spelling mistakes in this text.

Language:
{language}

Rules:

- Preserve the exact meaning.
- Do not add new information.
- Do not change the user's intention.
- Keep Tamil written in English letters naturally.
- Keep English words correct.
- Do not explain anything.
- Return ONLY the corrected text.

Text:
{text}
"""

    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise spelling "
                    "correction assistant."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1,

        max_completion_tokens=500
    )

    corrected_text = (
        response
        .choices[0]
        .message
        .content
    )

    return corrected_text.strip()


# ============================================================
# MAIN TOURIST AI
# ============================================================

def ask_tourist_ai(
    user_message: str,
    voice: str = "JARVIS",
    language: str = "Tamil + English",
    chat_history: list = None
) -> str:
    """
    Ask Tourist AI.

    Supports:
    - JARVIS personality
    - EDY personality
    - Tamil + English
    - Previous chat context
    """

    if not user_message or not user_message.strip():

        return (
            "Please ask me something first. 🙂"
        )

    client = get_groq_client()

    voice = voice.upper()

    # ========================================================
    # PERSONALITY
    # ========================================================

    if voice == "JARVIS":

        personality = """
You are JARVIS, Tourist AI's premium travel assistant.

Personality:
- Calm
- Intelligent
- Professional
- Precise
- Helpful

Speak naturally and confidently.
"""

    else:

        personality = """
You are EDY, Tourist AI's friendly AI companion.

Personality:
- Friendly
- Energetic
- Casual
- Helpful
- Easy to talk to

Speak naturally like a smart travel friend.
"""

    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = f"""
{personality}

You are Tourist AI.

You help users with:

- Trip planning
- Tourist places
- Travel routes
- Budget planning
- Fuel estimates
- Hotels and stays
- Restaurants and food places
- Travel tips
- Day-by-day itineraries
- General travel questions

Language preference:
{language}

IMPORTANT RULES:

- Understand spelling mistakes automatically.
- Understand Tamil written using English letters.
- Reply naturally in Tamil + English when requested.
- Keep answers clear and practical.
- Do not invent live weather.
- Do not invent live prices.
- Do not invent exact hotel or restaurant availability.
- Clearly mention when information is only an estimate.
- If location information is uncertain,
  clearly say so.
"""

    # ========================================================
    # MESSAGES
    # ========================================================

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # ========================================================
    # PREVIOUS CHAT HISTORY
    # ========================================================

    if chat_history:

        for chat in chat_history[-10:]:

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

    # ========================================================
    # CURRENT QUESTION
    # ========================================================

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # ========================================================
    # AI RESPONSE
    # ========================================================

    response = client.chat.completions.create(

        model=MODEL_NAME,

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
