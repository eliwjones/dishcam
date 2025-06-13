import os
from pathlib import Path


from .util import wyze as wz
from .dishcam import ask_about_image, download_jpg, load_state, save_state
from .dishcam import CAMERA_MODEL, CAMERA_MAC, STATE_FILE
from .auth import email, password, key_id, api_key


def main():
    state = load_state(STATE_FILE, CAMERA_MAC, CAMERA_MODEL)
    print("Loaded state:", state)

    access_token, refresh_token, user_id = wz.login(email, password, key_id, api_key)
    recent_events = wz.recent_events(access_token, refresh_token, user_id, CAMERA_MAC, minutes=60)
    recent_events.sort(key=lambda event: event["event_ts"])

    print("Found events:", len(recent_events))

    for event in recent_events:
        event_id = event["event_id"]
        if event_id in state["processed"]:
            continue

        first_jpg = next((file for file in event["file_list"] if file["type"] == 1), None)
        if not first_jpg:
            state["processed"][event_id] = "skip"
            continue

        image_path = download_jpg(first_jpg['url'])
        answer = ask_about_image(image_path, "is there a dish in the sink")
        os.remove(image_path)

        print(f"image_path: {first_jpg['url']}, Answer: {answer}")

        if "yes" in answer.lower():
            previous_no_event_id = state.get("last_no_event_id")
            if previous_no_event_id:
                previous_event = next((ev for ev in recent_events if ev["event_id"] == previous_no_event_id), None)
                if previous_event:
                    start_ms, end_ms = wz.kvs_times(previous_event)
                    mpd_url = wz.dash_mpd(access_token, device_id=CAMERA_MAC, model=CAMERA_MODEL, start_ms=start_ms, end_ms=end_ms)
                    print("Dish appeared – MPD:", mpd_url)

                    state["cutovers"].append(
                        {
                            "clean_event_id": previous_no_event_id,
                            "dirty_event_id": event_id,
                            "start_ms": start_ms,
                            "end_ms": end_ms,
                            "transition_ts": event["event_ts"],
                        }
                    )

            state["processed"][event_id] = "yes"
            continue

        state["processed"][event_id] = "no"
        state["last_no_event_id"] = event_id

    save_state(state, STATE_FILE)


if __name__ == "__main__":
    main()
