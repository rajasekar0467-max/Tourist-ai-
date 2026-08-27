import os
import streamlit.components.v1 as components


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

COMPONENT_DIR = os.path.join(
    BASE_DIR,
    "voice_component_frontend"
)


voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)
