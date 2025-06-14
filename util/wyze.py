import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request


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

    body_json = json.dumps(body).encode('utf-8')

    req = urllib.request.Request(AUTH, headers=hdr, data=body_json, method="POST")
    with urllib.request.urlopen(req, timeout=10) as response:
        status = response.getcode()
        response_content = response.read().decode('utf-8')

    if status >= 400:
        raise urllib.error.HTTPError(AUTH, status, f"HTTP Error: {status}", response.headers, None)

    resp_json = json.loads(response_content)

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

    body_json = json.dumps(body).encode('utf-8')

    req = urllib.request.Request(EVENT, headers={"Content-Type": "application/json"}, data=body_json, method="POST")
    with urllib.request.urlopen(req, timeout=10) as response:
        status = response.getcode()
        response_content = response.read().decode('utf-8')

    if status >= 400:
        raise urllib.error.HTTPError(EVENT, status, f"HTTP Error: {status}", response.headers, None)

    resp_json = json.loads(response_content)

    return resp_json.get("data", {}).get("event_list", [])


def kvs_times(evt: dict) -> tuple[int, int]:
    p = evt.get("event_params", {})
    if "beginTime" in p and "endTime" in p:
        return int(p["beginTime"]), int(p["endTime"])

    for res in evt.get("event_resources", []):
        if res.get("resource_type") == "kvs":
            return int(res["begin_time"]), int(res["end_time"])

    raise KeyError("no KVS timestamps in event")


def dash_mpd(access_token: str, device_id: str, model: str, start_ms: int, end_ms: int) -> str:
    params = {
        "device_id": device_id,
        "product_model": model,
        "start_time": start_ms,
        "end_time": end_ms,
        "resource_type": "kvs",
        "resource_version": 0,
        "is_live": "false",
    }

    query_string = urllib.parse.urlencode(params)
    url_with_params = f"{REPLAY_URL}?{query_string}"

    req = urllib.request.Request(url_with_params, headers={"Authorization": access_token}, method="GET")
    with urllib.request.urlopen(req, timeout=10) as response:
        status = response.getcode()
        response_content = response.read().decode('utf-8')

    if status >= 400:
        raise urllib.error.HTTPError(url_with_params, status, f"HTTP Error: {status}", response.headers, None)

    resp_json = json.loads(response_content)

    return resp_json["data"]
