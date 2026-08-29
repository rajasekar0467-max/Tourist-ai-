import streamlit as st
from groq import Groq

from src.news.news_service import (
    is_news_query,
    is_current_office_query,
    extract_news_topic,
    get_live_news,
    format_news_for_ai
)


MODEL_NAME = "openai/gpt-oss-20b"


CURRENT_INFO_FALLBACK = (
    "I don't have a reliable live source to verify this "
    "information right now, so I don't want to give you an "
    "outdated answer."
)


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
# (kept available / unchanged; not required in the main flow
# since the system prompt already asks the model to understand
# spelling mistakes and Tanglish naturally)
# ============================================================

def correct_spelling(
    text: str,
    language: str = "Tamil + English"
) -> str:

    if not text or not text.strip():

        return text

    client = get_groq_client()

    prompt = f"""
Correct only obvious spelling mistakes.

Language:
{language}

Rules:

- Preserve the exact meaning.
- Do not add information.
- Keep Tamil written in English letters natural.
- Keep English words correct.
- Do not explain anything.
- Return only the corrected text.

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
# PERSONALITY BUILDER
#
# FRIDAY is the only personality in this app. The "voice"
# parameter is kept for compatibility with existing calls in
# app.py (which always passes voice="FRIDAY"), but it no longer
# switches between different personas (JARVIS / EDY) — it always
# builds the FRIDAY persona.
# ============================================================

def get_personality(
    voice: str,
    ai_type: str = "tourist"
):

    base_personality = """
You are FRIDAY, an intelligent AI assistant.

Personality:
- Warm
- Calm
- Intelligent
- Friendly
- Natural
- Professional when needed
- Conversational, not robotic

You do not constantly introduce yourself. Speak naturally,
like a knowledgeable friend who happens to be very well
informed.
"""

    if ai_type == "general":

        return f"""
{base_personality}

You are an advanced general-purpose AI assistant.

You can help with:

- General questions
- Education
- Coding
- Programming
- Technology
- Ideas
- Writing
- Explanations
- Daily life questions
- Travel
- Problem solving
- Creative thinking

You are NOT limited to tourism.

Answer naturally based on the user's question.
"""

    return f"""
{base_personality}

Right now you are helping with Tourist AI.

Your main expertise here is:

- Trip planning
- Tourist places
- Travel routes
- Budget planning
- Fuel estimates
- Hotels and stays
- Restaurants
- Travel tips
- Day-by-day itineraries
"""


# ============================================================
# SHARED LANGUAGE / QUALITY RULES
# ============================================================

def build_core_rules() -> str:

    return """
LANGUAGE UNDERSTANDING:

- Understand normal English.
- Understand Tamil.
- Understand Tamil written using English letters (Tanglish).
- Understand mixed Tamil + English.
- Understand spelling mistakes and typos naturally, without
  commenting on them.
- Reply naturally in the same language/style the user used.

ANSWER QUALITY:

- Answer directly first, then explain further only if it helps.
- Use headings and bullet points only when they genuinely
  improve clarity — not for every answer.
- Keep simple questions short. Give more detail for complex
  questions.
- Use the conversation history to understand follow-up
  questions and avoid repeating information you already gave.
- Distinguish clearly between facts, estimates, and opinions.
- Never invent facts. Never state uncertain information
  confidently.
- If something cannot be verified, say so plainly instead of
  guessing.
- Ask a clarifying question only when it is genuinely necessary
  to give a correct answer — otherwise just answer.
"""


# ============================================================
# MAIN TOURIST AI
# ============================================================

def ask_tourist_ai(
    user_message: str,
    voice: str = "FRIDAY",
    language: str = "Tamil + English",
    chat_history: list = None
) -> str:

    if not user_message or not user_message.strip():

        return (
            "Please ask me something first. 🙂"
        )

    client = get_groq_client()

    personality = get_personality(
        voice,
        "tourist"
    )

    system_prompt = f"""
{personality}

{build_core_rules()}

Language preference:
{language}

TOURIST-SPECIFIC RULES:

- Focus mainly on travel-related questions.
- Do not invent live weather.
- Do not invent live prices.
- Do not invent exact hotel availability.
- Clearly mention estimates when needed.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

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

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

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


# ============================================================
# GENERAL CHAT AI
# ============================================================

def ask_general_ai(
    user_message: str,
    voice: str = "FRIDAY",
    language: str = "Tamil + English",
    chat_history: list = None
) -> str:

    if not user_message or not user_message.strip():

        return (
            "Enna venum nu kelu macha 🙂"
        )

    # ========================================================
    # CURRENT OFFICE-HOLDER GUARD
    # (e.g. "who is the current chief minister")
    # Answered directly, without the model guessing, unless the
    # user is clearly asking for a *news* story about it — in
    # that case the live news flow below handles it.
    # ========================================================

    if (
        is_current_office_query(user_message)
        and not is_news_query(user_message)
    ):

        return CURRENT_INFO_FALLBACK

    client = get_groq_client()

    personality = get_personality(
        voice,
        "general"
    )

    # ========================================================
    # LIVE NEWS RETRIEVAL
    # ========================================================

    news_context = ""
    news_error = ""

    if is_news_query(user_message):

        try:

            topic = extract_news_topic(user_message)

            articles = get_live_news(topic)

            news_context = format_news_for_ai(articles)

        except Exception as error:

            news_error = str(error)

    system_prompt = f"""
{personality}

{build_core_rules()}

Language preference:
{language}

CURRENT INFORMATION RULES:

- Never pretend to have live information when you do not have
  it.
- Do not guess who currently holds a political or corporate
  office (Chief Minister, Prime Minister, President, CEO, etc.)
  unless it is explicitly confirmed by the NEWS_DATA provided to
  you in this conversation. If it is not confirmed there, say:
  "{CURRENT_INFO_FALLBACK}"
"""

    if news_context:

        system_prompt += """
A NEWS_DATA message with live news articles has been provided
to you below. When answering:

- Answer only using the NEWS_DATA provided — do not mix in old
  model knowledge unless you clearly label it as background
  information.
- Mention the source name when useful.
- Mention the publication time when available.
- If the NEWS_DATA doesn't actually answer the user's question,
  say so honestly instead of guessing.
"""

    if news_error:

        system_prompt += f"""
Live news could not be retrieved right now
(reason: {news_error}). Clearly tell the user that live news is
currently unavailable — do not invent news content.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if news_context:

        messages.append(
            {
                "role": "system",
                "content": f"NEWS_DATA:\n{news_context}"
            }
        )

    if chat_history:

        for chat in chat_history[-15:]:

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

        model=MODEL_NAME,

        messages=messages,

        temperature=0.75,

        max_completion_tokens=1500
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    return answer.strip()
