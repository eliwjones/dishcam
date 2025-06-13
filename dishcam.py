from google import genai
from google.genai import types

from .auth import email, password, key_id, api_key, gemini_api_key


def ask_about_image(img_path: str, question: str):
    client = genai.Client(api_key=gemini_api_key)

    with open(img_path, "rb") as fh:
        img_bytes = fh.read()

    img_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

    contents = [img_part, question]

    response = client.models.generate_content(model="gemini-1.5-flash", contents=contents)
    return response.text
