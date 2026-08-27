import os
import streamlit.components.v1 as components


# ============================================================
# FRIDAY VOICE COMPONENT
# ============================================================

COMPONENT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "frontend"
)


voice_assistant_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)
