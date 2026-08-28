import os
import streamlit.components.v1 as components


# Project root:
# tourist-ai-/
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# tourist-ai-/voice_component_frontend/
COMPONENT_DIR = os.path.join(
    BASE_DIR,
    "voice_component_frontend"
)


# Check folder exists
if not os.path.isdir(COMPONENT_DIR):

    raise FileNotFoundError(
        f"FRIDAY component folder not found: "
        f"{COMPONENT_DIR}"
    )


# Check index.html exists
INDEX_FILE = os.path.join(
    COMPONENT_DIR,
    "index.html"
)


if not os.path.isfile(INDEX_FILE):

    raise FileNotFoundError(
        f"FRIDAY index.html not found: "
        f"{INDEX_FILE}"
    )


voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)
