from google import genai
from google.genai import types

from .auth import email, password, key_id, api_key, gemini_api_key


def ask_about_image(img_path: str, question: str) -> str:
    client = genai.Client(api_key=gemini_api_key)

    with open(img_path, "rb") as fh:
        img_bytes = fh.read()

    img_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

    contents = [img_part, question]

    response = client.models.generate_content(model="gemini-1.5-flash", contents=contents)
    return response.text


"""

from auth import email, password, key_id, api_key
import util.wyze as wz


mac = 'D03F27511BDF'
access_token, refresh_token, user_id = wz.login(email, password, key_id, api_key)

events = wz.recent_events(access_token, refresh_token, user_id, mac, minutes=30)

start_ms, end_ms = wz.kvs_times(events[0])
wz.dash_mpd(access_token, device_id=mac, model="WYZE_CAKP2JFUS", start_ms=start_ms, end_ms=end_ms)

"""
