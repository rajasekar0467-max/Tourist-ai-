import os
import streamlit.components.v1 as components


CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

COMPONENT_DIR = os.path.join(
    CURRENT_DIR,
    "voice_component_frontend"
)


INDEX_FILE = os.path.join(
    COMPONENT_DIR,
    "index.html"
)


if not os.path.exists(COMPONENT_DIR):
    raise RuntimeError(
        f"Voice component folder not found: {COMPONENT_DIR}"
    )


if not os.path.exists(INDEX_FILE):
    raise RuntimeError(
        f"index.html not found: {INDEX_FILE}"
    )


voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)
