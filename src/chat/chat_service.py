from src.ai.groq_service import ask_tourist_ai


def ask_general_ai(
    user_message: str,
    voice: str = "JARVIS",
    chat_history=None
):
    """
    General-purpose AI chatbot.

    Supports:
    - Tamil
    - English
    - Coding
    - Education
    - Technology
    - General questions
    - Casual conversation
    - Travel and more
    """

    if not user_message or not user_message.strip():
        return "Please ask me something."

    if chat_history is None:
        chat_history = []

    voice = voice.upper()

    if voice == "EDY":

        personality = """
You are EDY, a friendly, energetic and helpful
general AI assistant.

Speak naturally and casually.

You can understand Tamil, English and Tanglish.
"""

    else:

        personality = """
You are JARVIS, a calm, intelligent and professional
general AI assistant.

Speak naturally, clearly and helpfully.

You can understand Tamil, English and Tanglish.
"""

    conversation = ""

    # Keep recent conversation for context
    recent_history = chat_history[-10:]

    for chat in recent_history:

        user_text = chat.get("user", "")
        assistant_text = chat.get("assistant", "")

        conversation += f"""
User: {user_text}
Assistant: {assistant_text}
"""

    prompt = f"""
{personality}

You are a general-purpose AI chatbot.

You are NOT limited to tourism or travel.

You can help with:
- General questions
- Coding
- Python
- Computer Science
- Education
- Technology
- Ideas
- Writing
- Explanations
- Travel
- Casual conversation

Important language rules:

- Understand Tamil.
- Understand English.
- Understand Tanglish.
- Reply in the same language style preferred
  by the user whenever possible.
- Keep answers clear and natural.

Previous conversation:

{conversation}

Current user message:

{user_message}

Give a helpful and natural response.
"""

    return ask_tourist_ai(
        prompt,
        voice=voice,
        language="Tamil + English",
        chat_history=[]
    )
