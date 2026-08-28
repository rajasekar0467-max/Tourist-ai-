import os
import streamlit.components.v1 as components


# src/voice_component.py
# Project root = parent of src folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

COMPONENT_DIR = os.path.join(
    BASE_DIR,
    "voice_component_frontend"
)


# Helpful error instead of mysterious Streamlit error
if not os.path.isdir(COMPONENT_DIR):
    raise FileNotFoundError(
        "voice_component_frontend folder not found.\n"
        f"Expected location: {COMPONENT_DIR}"
    )


INDEX_FILE = os.path.join(
    COMPONENT_DIR,
    "index.html"
)

if not os.path.isfile(INDEX_FILE):
    raise FileNotFoundError(
        "index.html not found.\n"
        f"Expected location: {INDEX_FILE}"
    )


voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)
