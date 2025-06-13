from datetime import datetime, timedelta

from google import genai
from google.genai import types
from wyze_sdk import Client
from wyze_sdk.models.events import EventFileType

from .auth import email, password, key_id, api_key, gemini_api_key


def ask_about_image(img_path: str, question: str) -> str:
    client = genai.Client(api_key=gemini_api_key)

    with open(img_path, "rb") as fh:
        img_bytes = fh.read()

    img_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

    contents = [img_part, question]

    response = client.models.generate_content(model="gemini-1.5-flash", contents=contents)
    return response.text


def get_client(email, password, key_id, api_key):
    return Client(email=email, password=password, key_id=key_id, api_key=api_key)


def dishcam_events(client: Client):
    camera = client.cameras.list()[0]

    events = client.events.list(device_ids=[camera.mac], begin=datetime.now() - timedelta(minutes=30), end=datetime.now())
    events_data = []
    for event in events:
        event_data = {}
        for file in event.files:
            file_type = file.type
            if not file_type or file_type not in [EventFileType.IMAGE, EventFileType.VIDEO]:
                continue

            _type = 'jpg'
            if file_type == EventFileType.VIDEO:
                _type = 'video'

            date_str = datetime.fromtimestamp(event.time / 1000).strftime("%B %d, %Y at %I:%M:%S %p")

            event_data[_type] = file.url
            event_data['date_str'] = date_str
        events_data.append(event_data)

    return events_data, events


"""
from dishcam.auth import *
from dishcam import dishcam as dc

client = dc.get_client(email, password, key_id, api_key)
events_data, events = dc.dishcam_events(client)

for event in events_data:
    print(event)


# 4:23PM video has dish bandit.


https://prod-sight-safe-auth.wyze.com/resource/D03F27511BDF/2025-06-12/D03F27511BDF131749771089_1749771089666_13_1_0/1abe69d31a0f456d8f49374f54849c86_-1.jpg?st=RR6IOV-zF7vLqdja92dZpFKDktVU4YFKmmzQKaF0MPT2Ava2jBqOckg7vdeRL_LqMPliGvzzI0SRN_W6aspjq1l31o1kHqNuGfGuFNt72Kkk4b0GVLBrT95_RCsdghTXHr-32qG7AhG6t_oa4koqbUtzzVDl3PMwxQP_nuKfL7Tn_xMFieKGMxLzcaKIgPpFyH1XEvsI47CNjS7adpEKtUYFSzDgN9UOxaob0Ex70utBP3y2yrqlTCRHBb8wXR_Ir_hmRsYicn7_gzdeR7YWlvMDBucxaXm9EntSyXlpFELUfPsxH1lLY1qmq27XRq7ZT9J9I1wxaAyCxw&kid=jkdDoe8hiqZgxbesRUgaR2&nonce=rX0p71dDHukwTW3l
https://prod-sight-safe-auth.wyze.com/resource/D03F27511BDF/2025-06-12/D03F27511BDF131749771089_1749771089666_13_2_0/726516ebd7ef47f7a4a6e8126fc76a2d_-1.mp4?st=2PCg3EDQK8qLSrOpArVi8e-FKFYoAwUdwVtsEvx4ry9YzL9hLQSv-TzxhAN6K_jT3mYJAFByljpPagGWFQDKYteN_VjFd3ejLmI4WMCFg8r3ZTB5HTwAwmaVMBOnAIjxkT05466Llcn9K2NScllbQsrAb01g5TY3hymKfnoIS61AE_Qs7yiaqJzlx8RtmOcEi0yC8MekrhxrovP4GL0E7kFPwUoUyIgk9xY4t0xxpY_nQnCHS7WP3Q2gRkZ3zlHvfmnStLAMID673_eMkc3EsvbwfGOWX6sIWoyhWydTa4UOvJGjrPFyngFMij2OVJy0DrMuBBrOOFkchw&kid=jkdDoe8hiqZgxbesRUgaR2&nonce=vM4ynaQU8oQlCZH_

<ErrorResponse>
<description>File not exist.</description>
<requestId>3bf11763-67a3-4391-89af-ad34c835f01b</requestId>
<errorCode>5000</errorCode>
</ErrorResponse>


response = ask_about_image("path/to/image.jpg", "Are there dishes in the sink?")

"""
