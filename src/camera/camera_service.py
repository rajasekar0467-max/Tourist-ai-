import base64
import io

from PIL import Image


def validate_tourist_image(image_file):
    """
    Validate and prepare an uploaded/camera image.
    """

    if image_file is None:
        return {
            "success": False,
            "message": "No image selected."
        }

    try:
        image = Image.open(image_file)

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


def image_to_base64(image):
    """
    Convert a PIL image to base64.

    This format can be passed to a compatible
    vision API later.
    """

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=85
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return encoded


def create_place_analysis_prompt():
    """
    Prompt for tourist-place image analysis.
    """

    return """
You are Tourist AI.

Analyze the provided travel image carefully.

Try to identify visible landmarks, buildings,
landscapes, signs, monuments, temples, beaches,
mountains, roads or other tourist features.

Give the answer in Tamil + English.

Provide:

1. Possible place or landmark
2. City / state / country if identifiable
3. What the place is famous for
4. Short historical or cultural information
5. Best time to visit
6. Nearby attractions
7. Tourist tips
8. Things to be careful about

IMPORTANT:

- Do not claim an exact location unless the image
  provides enough evidence.
- If uncertain, clearly say "Possible match".
- Never invent details.
- Separate confirmed observations from guesses.
"""


def prepare_image_for_vision(image_file):
    """
    Validate the image and prepare it for a
    vision-capable AI service.
    """

    result = validate_tourist_image(
        image_file
    )

    if not result["success"]:
        return result

    image = result["image"]

    encoded_image = image_to_base64(
        image
    )

    return {
        "success": True,
        "image": image,
        "base64": encoded_image,
        "width": image.width,
        "height": image.height,
        "prompt": create_place_analysis_prompt()
    }
