import os
import streamlit.components.v1 as components


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

COMPONENT_DIR = os.path.join(
    CURRENT_DIR,
    "voice_component_frontend"
)


_voice_component = components.declare_component(
    "tourist_ai_voice",
    path=COMPONENT_DIR
)


def voice_assistant_component(
    running=False,
    language="ta-IN",
    audio_b64="",
    status="READY TO LISTEN",
    key=None
):

    result = _voice_component(
        running=running,
        language=language,
        audio_b64=audio_b64,
        status=status,
        key=key,
        default={}
    )

    if result is None:
        return {}

    return result
