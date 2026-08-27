from pathlib import Path
import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent / "voice_component_frontend"
_component = components.declare_component(
    "tourist_ai_voice",
    path=str(_COMPONENT_DIR),
)


def voice_assistant_component(
    *,
    key="tourist_voice",
    running=False,
    language="ta-IN",
    audio_b64="",
    status="READY TO LISTEN",
):
    """ChatGPT-style voice orb. Returns {text, event_id} when speech is captured."""
    return _component(
        key=key,
        running=running,
        language=language,
        audio_b64=audio_b64 or "",
        status=status,
        default_value=None,
    )
