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

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=500
    )

    return response.choices[0].message.content
