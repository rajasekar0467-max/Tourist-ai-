from PIL import Image


def validate_tourist_image(image_file):
    """
    Validate and prepare a tourist-place image.
    """

    if image_file is None:
        return {
            "success": False,
            "message": "No image selected."
        }

    try:
        image = Image.open(image_file)

        # Convert to RGB for consistent processing
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


def create_place_analysis_prompt():
    """
    Prompt used when the image-analysis AI is connected.
    """

    return """
Analyze this tourist/travel image.

Try to determine what is visible in the image.

Provide:

1. Possible place or landmark
2. Country/state/city if identifiable
3. What the place is known for
4. Short interesting history
5. Best time to visit
6. Nearby attractions
7. Useful tourist tips

If the exact location cannot be determined,
clearly say that it is only a possibility.

Do not pretend to know the exact location
when the image does not provide enough evidence.
"""
