import os
import tempfile
import requests


def text_to_speech(text: str, voice_name: str = "JARVIS"):
    """
    Convert text to speech.

    This is a provider-ready function.
    Add a supported TTS provider later through
    environment variables.
    """

    api_key = os.getenv("TTS_API_KEY")
    api_url = os.getenv("TTS_API_URL")

    if not api_key or not api_url:
        return {
            "success": False,
            "message": (
                "TTS provider is not configured yet."
            ),
            "audio_path": None
        }

    voice_name = voice_name.upper()

    if voice_name == "EDY":
        voice_id = os.getenv(
            "EDY_VOICE_ID",
            "edy-original"
        )
    else:
        voice_id = os.getenv(
            "JARVIS_VOICE_ID",
            "jarvis-original"
        )

    try:

        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "voice": voice_id
            },
            timeout=30
        )

        response.raise_for_status()

        audio_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )

        audio_file.write(response.content)
        audio_file.close()

        return {
            "success": True,
            "message": "Voice generated successfully.",
            "audio_path": audio_file.name
        }

    except requests.RequestException as error:

        return {
            "success": False,
            "message": f"Voice generation failed: {error}",
            "audio_path": None
        }
