import json

from pathlib import Path

import requests
import tempfile

from google import genai
from google.genai import types

from .auth import email, password, key_id, api_key, gemini_api_key
from .util import wyze as wz


STATE_FILE = Path("dishcam_state.json")
CAMERA_MODEL = "WYZE_CAKP2JFUS"
CAMERA_MAC = "D03F27511BDF"


def ask_about_image(img_path: str, question: str):
    client = genai.Client(api_key=gemini_api_key)

    with open(img_path, "rb") as fh:
        img_bytes = fh.read()

    img_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

    contents = [img_part, question]

    response = client.models.generate_content(model="gemini-1.5-flash", contents=contents)
    return response.text


def load_state(state_file, camera_mac, camera_model):
    if state_file.exists():
        with state_file.open() as file_handle:
            return json.load(file_handle)

    return {
        "camera_mac": camera_mac,
        "camera_model": camera_model,
        "events": {},
        "processed": {},
        "last_no_event_id": None,
        "cutovers": [],
    }


def save_state(state, state_file):
    with state_file.open("w") as file_handle:
        json.dump(state, file_handle)


def download_jpg(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://my.wyze.com/",
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_file.write(response.content)
    temp_file.close()
    return temp_file.name


def fresh_cutover_mpd(index: int = -1, state_path="dishcam_state.json") -> str:
    with open(state_path) as fh:
        state = json.load(fh)

    try:
        cutover = state["cutovers"][index]
    except IndexError:
        raise ValueError("No cutover stored at that index")

    access_token, *_ = wz.login(email, password, key_id, api_key)

    return wz.dash_mpd(
        access_token, device_id=state["camera_mac"], model=state["camera_model"], start_ms=cutover["start_ms"], end_ms=cutover["end_ms"]
    )
