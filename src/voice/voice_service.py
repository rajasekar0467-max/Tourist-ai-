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

    voice_name = voice_name.upper()

    if voice_name not in VOICE_PROFILES:
        voice_name = "JARVIS"

    return VOICE_PROFILES[voice_name]


def prepare_voice_text(
    text: str,
    voice_name: str = "JARVIS"
):

    profile = get_voice_profile(voice_name)

    return {
        "voice": voice_name.upper(),
        "style": profile["style"],
        "description": profile["description"],
        "text": text
    }
