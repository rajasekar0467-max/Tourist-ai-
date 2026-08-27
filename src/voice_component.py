import os
import streamlit.components.v1 as components


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.dirname(CURRENT_DIR)

COMPONENT_DIR = os.path.join(
    PROJECT_DIR,
    "voice_component_frontend"
)


if not os.path.exists(COMPONENT_DIR):
    raise FileNotFoundError(
        f"Voice component folder not found: {COMPONENT_DIR}"
    )


INDEX_FILE = os.path.join(
    COMPONENT_DIR,
    "index.html"
)


if not os.path.exists(INDEX_FILE):
    raise FileNotFoundError(
        f"index.html not found: {INDEX_FILE}"
    )


voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)
