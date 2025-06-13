import hashlib
import requests
import time


AUTH = "https://auth-prod.api.wyze.com/api/user/login"
EVENT = "https://api.wyzecam.com/app/v2/device/get_event_list"
GRAPH = "https://prod-api.wyze.com/graphql"


def _triple_md5(text: str) -> str:
    for _ in range(3):
        text = hashlib.md5(text.encode()).hexdigest()
    return text


def login(email, password, key_id, api_key) -> str:
    hdr = {"KeyId": key_id, "ApiKey": api_key, "Content-Type": "application/json"}
    body = {"email": email, "password": _triple_md5(password)}
    res = requests.post(AUTH, headers=hdr, json=body, timeout=10)
    res.raise_for_status()
    return res.json()["access_token"]


def recent_events(token: str, device_mac: str, minutes=10, max_count=50) -> list:
    end = int(time.time() * 1000)
    beg = end - minutes * 60_000
    body = {
        "access_token": token,
        "device_mac_list": [device_mac],
        "begin_time": beg,
        "end_time": end,
        "order_by": 2,  # newest-first
        "count": max_count,
        "app_ver": "wyze_developer_api",
        "app_version": "wyze_developer_api",
        "phone_id": "wyze_developer_api",
        "sc": "wyze_developer_api",
        "sv": "wyze_developer_api",
        "ts": end,
    }
    res = requests.post(EVENT, json=body, timeout=10)
    res.raise_for_status()
    return res.json().get("data", {}).get("event_list", [])


def video_file_ids(event: dict) -> list:
    return [f["file_id"] for f in event.get("file_list", []) if f.get("type") == 2 and f.get("status", 1) == 1]  # 2 = VIDEO


def playback_url(token: str, event_id: str) -> str:
    query = """
    query($eventId: String!) {
      getEventPlaybackUrl(eventId: $eventId) {
        url
      }
    }
    """
    hdr = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.post(GRAPH, headers=hdr, json={"query": query, "variables": {"eventId": event_id}}, timeout=10)
    res.raise_for_status()
    return res.json()["data"]["getEventPlaybackUrl"]["url"]


def save_mp4(url: str, path: str) -> str:
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(path, "wb") as fh:
            for chunk in r.iter_content(1 << 14):
                if chunk:
                    fh.write(chunk)
    return path


"""
from ..auth import email, password, key_id, api_key

mac = 'D03F27511BDF'
token = login(email, password, key_id, api_key)
events = recent_events(token, mac)

evt = "D03F27511BDF131749775238"
tok = login(email, password, key_id, api_key)
clip = save_mp4(playback_url(tok, evt), f"{evt}.mp4")
print("saved", clip)
"""
