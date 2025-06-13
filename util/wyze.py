"""
util/wyze.py  –  minimal Wyze-cloud helper
Env vars: WYZE_EMAIL, WYZE_PASSWORD, WYZE_KEY_ID, WYZE_API_KEY
"""
import hashlib, os, time, requests

AUTH = "https://auth-prod.api.wyze.com/api/user/login"
EVENT = "https://api.wyzecam.com/app/v2/device/get_event_list"
REPLAY_URL = "https://kvs-service.wyzecam.com/app/v4/replay_url"


def _triple_md5(txt: str) -> str:
    for _ in range(3):
        txt = hashlib.md5(txt.encode()).hexdigest()
    return txt


def login(email, password, key_id, api_key):
    hdr = {"KeyId": key_id, "ApiKey": api_key, "Content-Type": "application/json"}
    body = {"email": email, "password": _triple_md5(password)}
    res = requests.post(AUTH, headers=hdr, json=body, timeout=10)
    res.raise_for_status()

    resp_json = res.json()

    return resp_json["access_token"], resp_json["refresh_token"], resp_json["user_id"]


def recent_events(token: str, refresh: str, user_id: str, mac: str, minutes=10, count=50) -> list:
    now = int(time.time() * 1000)
    body = {
        "access_token": token,
        "refresh_token": refresh,
        "user_id": user_id,
        "device_mac_list": [mac],
        "begin_time": now - minutes * 60_000,
        "end_time": now,
        "order_by": 1,
        "count": count,
        "app_ver": "wyze_developer_api",
        "app_version": "wyze_developer_api",
        "phone_id": "wyze_developer_api",
        "sc": "wyze_developer_api",
        "sv": "wyze_developer_api",
        "ts": now,
    }

    res = requests.post(EVENT, json=body, timeout=10)
    res.raise_for_status()

    return res.json().get("data", {}).get("event_list", [])


def video_file_ids(evt: dict) -> list[str]:
    return [f["file_id"] for f in evt.get("file_list", []) if f.get("type") in (2, 3) and f.get("status") in (1, 2)]


def save_mp4(url: str, path: str) -> str:
    with requests.get(url, stream=True, timeout=30) as r, open(path, "wb") as fh:
        r.raise_for_status()
        for chunk in r.iter_content(1 << 15):
            if chunk:
                fh.write(chunk)
    return path


"""

from auth import email, password, key_id, api_key
import util.wyze as wz


mac = 'D03F27511BDF'
access_token, refresh_token, user_id = wz.login(email, password, key_id, api_key)
events = wz.recent_events(access_token, refresh_token, user_id, mac, minutes=30)

"""
