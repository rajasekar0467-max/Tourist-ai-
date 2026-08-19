from src.services.groq_service import get_groq_client


def analyze_tourist_image(
    image_base64: str,
    prompt: str,
    voice: str = "JARVIS",
    language: str = "Tamil + English"
) -> str:
    """
    Analyze a tourist image using Groq Vision AI.
    """

    if not image_base64:
        return "❌ Image data is missing."

    client = get_groq_client()

    if voice == "JARVIS":
        personality = """
You are JARVIS, a calm, intelligent and professional
travel AI assistant.

Be precise, informative and organized.
"""

    else:
        personality = """
You are EDY, a friendly, energetic and helpful
travel AI assistant.

Be casual, positive and easy to understand.
"""

    system_prompt = f"""
{personality}

You are Tourist AI's visual travel assistant.

Analyze the uploaded tourist image carefully.

Language preference: {language}

Important rules:
- Do not pretend to know the exact location if the image
  does not provide enough evidence.
- Clearly separate observations from guesses.
- Never invent landmarks, history, distances or prices.
- If identification is uncertain, say "Possible match".
- Keep the answer useful for a tourist.
"""

    user_content = [
        {
            "type": "text",
            "text": prompt
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        }
    ]

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=0.3,
            max_tokens=1200
        )

        result = response.choices[0].message.content

        if not result:
            return "❌ Vision AI returned an empty response."

        return result.strip()

    except Exception as error:
        return f"❌ Vision AI error: {error}"


def analyze_prepared_image(
    prepared_image: dict,
    voice: str = "JARVIS",
    language: str = "Tamil + English"
) -> str:
    """
    Analyze the output returned by camera_service.prepare_image_for_vision().
    """

    if not prepared_image.get("success"):
        return prepared_image.get(
            "message",
            "❌ Unable to prepare the image."
        )

    return analyze_tourist_image(
        image_base64=prepared_image["base64"],
        prompt=prepared_image["prompt"],
        voice=voice,
        language=language
    )
