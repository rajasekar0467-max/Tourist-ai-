import os
import streamlit.components.v1 as components


# Project root folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# Frontend folder
COMPONENT_DIR = os.path.join(
    BASE_DIR,
    "voice_component_frontend"
)


# Streamlit custom component
voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)
