import base64
import io

from PIL import Image


def validate_tourist_image(image_file):
    """
    Validate uploaded or camera image.
    """

    if image_file is None:
        return {
            "success": False,
            "message": "No image selected."
        }

    try:
        image = Image.open(image_file)

        image.load()

        if image.mode != "RGB":
            image = image.convert("RGB")

        return {
            "success": True,
            "image": image,
            "width": image.width,
            "height": image.height
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Invalid image: {error}"
        }


def image_to_bytes(image):
    """
    Convert PIL image into JPEG bytes.
    """

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=90,
        optimize=True
    )

    return buffer.getvalue()


def image_to_base64(image_bytes):
    """
    Convert image bytes to Base64.
    """

    return base64.b64encode(
        image_bytes
    ).decode("utf-8")


def create_place_analysis_prompt():
    """
    Prompt instructions for Tourist AI Vision.
    """

    return """
You are Tourist AI.

Analyze the travel image carefully.

Provide:

1. 📍 Possible place or landmark
2. 👀 Clearly visible features
3. 🏛️ Historical or cultural information if known
4. 🌍 Possible city/state/country
5. 🎯 Things tourists can do there
6. 📅 Best time to visit
7. 📸 Nearby attractions if confidently known
8. 💡 Practical tourist tips

IMPORTANT:

- Do not claim an exact location without enough evidence.
- Clearly separate visible facts from guesses.
- If uncertain, say "Possible match".
- Never invent landmarks or locations.
"""


def prepare_image_for_vision(image_file):
    """
    Validate image and prepare all formats
    required by Vision AI.
    """

    result = validate_tourist_image(
        image_file
    )

    if not result["success"]:
        return result

    image = result["image"]

    image_bytes = image_to_bytes(
        image
    )

    encoded_image = image_to_base64(
        image_bytes
    )

    return {
        "success": True,
        "image": image,
        "image_bytes": image_bytes,
        "base64": encoded_image,
        "mime_type": "image/jpeg",
        "width": image.width,
        "height": image.height,
        "prompt": create_place_analysis_prompt()
    }
