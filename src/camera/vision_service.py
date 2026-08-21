import os
import base64

from groq import Groq


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
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
    Analyze a tourist/travel image using Groq Vision AI.

    Supports:
    - JPG
    - JPEG
    - PNG
    - WEBP
    """

    if not image_result.get("success"):
        return "❌ Image preparation failed."

    image_bytes = image_result.get("image_bytes")

    if not image_bytes:
        return "❌ Image data not found."

    # --------------------------------------------------------
    # Convert image to Base64
    # --------------------------------------------------------

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    mime_type = image_result.get(
        "mime_type",
        "image/jpeg"
    )

    image_data_url = (
        f"data:{mime_type};base64,{image_base64}"
    )

    # --------------------------------------------------------
    # Voice personality
    # --------------------------------------------------------

    if voice == "JARVIS":

        personality = """
You are JARVIS, a calm, intelligent and professional
AI travel assistant.

Be precise, helpful and informative.
"""

    else:

        personality = """
You are EDY, a friendly, energetic and casual
AI travel assistant.

Be helpful, enthusiastic and easy to understand.
"""

    # --------------------------------------------------------
    # Vision prompt
    # --------------------------------------------------------

    system_prompt = f"""
{personality}

You are Tourist AI's Camera Vision Assistant.

Your job is to analyze travel and tourist-place images.

When an image is provided:

1. Identify the visible place if reasonably possible.
2. If you cannot identify it exactly, clearly say so.
3. Describe important visible landmarks or features.
4. Explain what kind of place it appears to be.
5. Give useful tourist information.
6. Mention possible activities.
7. Give practical travel tips.
8. Do not invent exact facts when they are not visible
   or reasonably known.

Language:
{language}

For Tamil + English:
- Explain naturally using both Tamil and English.
- Keep the response easy for a Tamil-speaking traveller.

Format the answer clearly with headings and bullet points.
"""

    # --------------------------------------------------------
    # API request
    # --------------------------------------------------------

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

                        "text": """
Analyze this travel image.

Tell me:

📍 Place / Landmark
🧭 What I can see
🏞️ Why it is interesting
🎯 Things to do
💡 Tourist tips

If the exact location cannot be determined
from the image, say that clearly.
"""
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

        max_completion_tokens=1000

    )

    # --------------------------------------------------------
    # Return answer
    # --------------------------------------------------------

    return response.choices[0].message.content
