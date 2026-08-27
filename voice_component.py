import os
import streamlit.components.v1 as components

# Frontend folder path
_component_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "voice_component_frontend"
)

voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=_component_dir
)
