import base64
import io


VOICE_PROFILES = {
    "JARVIS": {
        "style": "calm, intelligent, professional, futuristic",
        "description": "Calm and professional travel assistant"
    },
    "EDY": {
        "style": "friendly, energetic, casual, helpful",
        "description": "Friendly and energetic travel companion"
    }
}


def get_voice_profile(voice_name: str):
    """
    Return the selected AI voice personality.
    """

    voice_name = voice_name.upper()

    if voice_name not in VOICE_PROFILES:
        voice_name = "JARVIS"

    return VOICE_PROFILES[voice_name]


def prepare_voice_text(
    text: str,
    voice_name: str = "JARVIS"
):
    """
    Prepare AI response text for the selected
    voice personality.

    Actual text-to-speech provider will be connected
    in the next stage.
    """

    profile = get_voice_profile(voice_name)

    return {
        "voice": voice_name.upper(),
        "style": profile["style"],
        "text": text
    }
