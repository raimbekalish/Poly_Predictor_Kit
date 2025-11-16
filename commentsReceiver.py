import requests
import time
import json

link = "https://polymarket.com/event/top-spotify-artist-2025-146?tid=1763271859630"
event_slug = link.split("/")[-1]
slug_resp = requests.get(f"https://gamma-api.polymarket.com/events/slug/{event_slug}")
slug_data = slug_resp.json()

BASE_URL = "https://gamma-api.polymarket.com/comments"
PARENT_TYPE = "Event"
PARENT_ID = slug_data.get("id")
LIMIT = 100

all_comments = []
offset = 0

while True:
    params = {
        "parent_entity_type": PARENT_TYPE,
        "parent_entity_id": PARENT_ID,
        "limit": LIMIT,
        "offset": offset
    }
    resp = requests.get(BASE_URL, params=params)
    resp.raise_for_status()
    page = resp.json()

    if not page:
        break

    all_comments.extend(page)
    offset += LIMIT

    time.sleep(0.2)

filtered = [
    {"body": c["body"]}
    for c in all_comments
]

with open('data.json', 'w') as f:
    json.dump(filtered, f, indent=4)

