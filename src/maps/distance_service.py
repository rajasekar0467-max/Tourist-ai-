import streamlit as st
from groq import Groq

from src.news.news_service import (
is_news_query,
get_live_news,
format_news_for_ai
)

MODEL_NAME = "openai/gpt-oss-20b"

============================================================
GROQ CLIENT
============================================================

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
============================================================
SPELLING CORRECTION
============================================================

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

Preserve the exact meaning.
Do not add information.
Keep Tamil written in English letters natural.
Keep English words correct.
Do not explain anything.
Return only the corrected text.

Text:
{text}
"""

response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {
            "role": "system",
            "content": "You are a precise spelling correction assistant."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.1,
    max_completion_tokens=500
)

corrected_text = response.choices[0].message.content

return corrected_text.strip()
============================================================
FRIDAY PERSONALITY
============================================================

def get_personality(
voice: str = "FRIDAY",
ai_type: str = "general"
):

return """

You are FRIDAY, an intelligent AI assistant.

Personality:

Warm
Intelligent
Friendly
Natural
Helpful
Conversational
Calm
Professional when needed

Important:

Your name is FRIDAY.
Never say you are JARVIS.
Never say you are EDY.
Do not mention multiple personalities.
Respond naturally according to the user's language and style.
Do not constantly introduce yourself.
"""
============================================================
MAIN TOURIST AI
============================================================

def ask_tourist_ai(
user_message: str,
voice: str = "FRIDAY",
language: str = "Tamil + English",
chat_history: list = None
) -> str:

if not user_message or not user_message.strip():
    return "Please ask me something first. 🙂"

client = get_groq_client()

personality = get_personality(
    "FRIDAY",
    "tourist"
)

system_prompt = f"""

{personality}

You are also a Tourist AI.

Your travel expertise:

Trip planning
Tourist places
Travel routes
Budget planning
Fuel estimates
Hotels and stays
Restaurants
Travel tips
Day-by-day itineraries

Language preference:
{language}

Rules:

Understand spelling mistakes automatically.
Understand Tamil written using English letters.
Understand mixed Tamil + English naturally.
Reply naturally in the user's language and style.
Keep answers clear and practical.
Focus mainly on travel-related questions.
Do not invent live weather.
Do not invent live prices.
Do not invent exact hotel availability.
Clearly mention estimates when needed.

If information is uncertain, say so.
"""

messages = [
{
"role": "system",
"content": system_prompt
}
]

if chat_history:

  for chat in chat_history[-10:]:

      user_text = chat.get("user", "")
      assistant_text = chat.get("assistant", "")

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

answer = response.choices[0].message.content

return answer.strip()

============================================================
GENERAL CHAT AI + LIVE NEWS
============================================================

def ask_general_ai(
user_message: str,
voice: str = "FRIDAY",
language: str = "Tamil + English",
chat_history: list = None
) -> str:

if not user_message or not user_message.strip():
    return "Enna venum nu kelu 🙂"

client = get_groq_client()

personality = get_personality(
    "FRIDAY",
    "general"
)

live_news_context = ""

# ========================================================
# LIVE NEWS DETECTION
# ========================================================

if is_news_query(user_message):

    try:

        articles = get_live_news(
            query=user_message,
            max_results=5
        )

        live_news_context = format_news_for_ai(
            articles
        )

    except Exception as error:

        live_news_context = (
            "LIVE NEWS UNAVAILABLE: "
            f"{error}"
        )

# ========================================================
# SYSTEM PROMPT
# ========================================================

system_prompt = f"""

{personality}

You are an advanced general-purpose AI assistant.

You can help with:

General questions
Education
Coding
Programming
Technology
Ideas
Writing
Explanations
Daily life questions
Travel
Problem solving
Creative thinking

Language preference:
{language}

ANSWER RULES:

Understand Tamil, English, Tamil written in English letters,
spelling mistakes, and mixed Tamil + English.
Answer naturally in the user's style when possible.
Answer directly first, then explain when useful.
Keep simple answers concise.
Give more detail for complex questions.
Explain difficult topics simply.
Do not invent facts.
Do not confidently state uncertain information.
Clearly distinguish facts from estimates or opinions.
Understand follow-up questions using the conversation history.
Avoid repeating information unnecessarily.
Ask a clarifying question only when truly necessary.

CURRENT INFORMATION RULE:

Your built-in knowledge may be outdated.
Never pretend that you have live information unless live data
is provided in the prompt.
For current facts such as current political office holders,
prices, availability, or recent events, do not guess.
If reliable live data is unavailable, clearly explain that you
cannot verify the latest information right now.

LIVE NEWS RULE:

If LIVE NEWS DATA is provided below, use it as the primary source
for current news.
Do not replace live news with old model knowledge.
Do not invent additional breaking news.
Mention source and publication time when useful.
If live news retrieval failed, clearly tell the user.

LIVE NEWS DATA:
{live_news_context if live_news_context else "No live news was requested."}
"""

messages = [
    {
        "role": "system",
        "content": system_prompt
    }
]

# ========================================================
# CHAT HISTORY
# ========================================================

if chat_history:

    for chat in chat_history[-15:]:

        user_text = chat.get("user", "")
        assistant_text = chat.get("assistant", "")

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

# ========================================================
# GROQ RESPONSE
# ========================================================

response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages,
    temperature=0.4,
    max_completion_tokens=1500
)

answer = response.choices[0].message.content

return answer.strip()
