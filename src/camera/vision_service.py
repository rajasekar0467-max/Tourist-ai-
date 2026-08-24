import os
import base64

from groq import Groq


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found."
        )

    return Groq(
        api_key=api_key
    )


# ============================================================
# VISION MODEL
# ============================================================

VISION_MODEL = "qwen/qwen3.6-27b"


# ============================================================
# ANALYZE IMAGE
# ============================================================

def analyze_prepared_image(
    image_result,
    voice="JARVIS",
    language="Tamil + English"
):
    """
    Analyze tourist/travel images using AI.
    """

    if not image_result.get("success"):

        return (
            "❌ Image preparation failed."
        )

    # --------------------------------------------------------
    # GET IMAGE DATA
    # --------------------------------------------------------

    image_bytes = image_result.get(
        "image_bytes"
    )

    if not image_bytes:

        return (
            "❌ Image data not found."
        )

    # --------------------------------------------------------
    # BASE64
    # --------------------------------------------------------

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    mime_type = image_result.get(
        "mime_type",
        "image/jpeg"
    )

    image_data_url = (
        f"data:{mime_type};base64,"
        f"{image_base64}"
    )

    # --------------------------------------------------------
    # AI PERSONALITY
    # --------------------------------------------------------

    if voice.upper() == "JARVIS":

        personality = """
You are JARVIS.

You are calm, intelligent, precise and professional.

Give structured and useful information.
"""

    else:

        personality = """
You are EDY.

You are friendly, energetic and helpful.

Explain things naturally and clearly.
"""

    # --------------------------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------------------------

    system_prompt = f"""
{personality}

You are Tourist AI's Camera Vision Assistant.

Your job is to analyze travel photographs.

Rules:

- Identify landmarks only when reasonably confident.
- Never invent an exact location.
- Clearly mention uncertainty.
- Separate visible observations from possible guesses.
- Give useful information for travellers.
- Keep answers easy to understand.

Language preference:
{language}

For Tamil + English:

Use natural Tamil mixed with English.
Keep the answer easy for Tamil-speaking travellers.

Use headings and bullet points.
"""

    # --------------------------------------------------------
    # USER PROMPT
    # --------------------------------------------------------

    user_prompt = """
Analyze this travel image carefully.

Give the answer using:

📍 Possible Place / Landmark

👀 What is Visible

🌍 Possible Location

🏛️ Interesting Information

🎯 Things To Do

📸 Nearby Attractions
(Only if reasonably confident)

📅 Best Time To Visit

💡 Tourist Tips

IMPORTANT:

If the exact location cannot be identified,
say clearly:

"Exact location cannot be confirmed from
this image alone."

Do not invent information.
"""

    # --------------------------------------------------------
    # AI REQUEST
    # --------------------------------------------------------

    try:

        client = get_groq_client()

        response = client.chat.completions.create(

            model=VISION_MODEL,

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",

                    "content": [

                        {
                            "type": "text",
                            "text": user_prompt
                        },

                        {
                            "type": "image_url",

                            "image_url": {
                                "url": image_data_url
                            }
                        }

                    ]
                }

            ],

            temperature=0.4,

            max_completion_tokens=1200
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        return answer

    except Exception as error:

        return (
            f"❌ Camera AI analysis failed: {error}"
        )
