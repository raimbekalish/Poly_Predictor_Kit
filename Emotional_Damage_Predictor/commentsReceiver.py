import requests
import time
import json
import os

def getComments(link):
    # Save NEXT TO this file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_PATH = os.path.join(BASE_DIR, "data.json")

    event_slug = link.split("/")[-1]
    slug_resp = requests.get(f"https://gamma-api.polymarket.com/events/slug/{event_slug}")
    slug_data = slug_resp.json()

    BASE_URL = "https://gamma-api.polymarket.com/comments"
    PARENT_TYPE = "Event"
    PARENT_ID = slug_data.get("id")
    LIMIT = 100

    if not PARENT_ID:
        print("Failed to extract event ID from slug API.")
        return

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

    filtered = [{"body": c.get("body", "")} for c in all_comments]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(filtered)} comments → {OUTPUT_PATH}")