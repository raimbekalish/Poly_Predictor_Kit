import os
import json
import time
from dotenv import load_dotenv
from google import genai


def geminiAutoClassifier():
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    BATCH_SIZE = 20
    INPUT_PATH = "./data.json"           # raw comments
    OUTPUT_PATH = "./data_labeled.json"  # progressive labeled file

    def gemini_label_classifier(batch):
        """Automatic label classifier to have data for training our own model"""

        batch_json = json.dumps(batch, ensure_ascii=False)
        prompt = f"""
        You are a strict comment classifier. You will receive an array of JSON objects, each with:
            - "body": the comment text
        
        For EACH comment, classify it as exactly ONE of:
            - "EMOTIONAL"
            - "RATIONAL"
            - "SPAM"

        Definitions (short):
            EMOTIONAL: emotion-heavy, opinions, little/no reasoning.
            RATIONAL: uses reasoning, facts, or structure to support claims.
            SPAM: off-topic, self-promo, nonsense, low-effort, "gm", etc.

        IMPORTANT:
        - Output MUST be valid JSON ONLY, no extra text.
        - Output format:
          [
            {{"message": <comment_text>, "label": "EMOTIONAL" | "RATIONAL" | "SPAM"}},
            ...
          ]

        Here is the input array of comments:
        {batch_json}
        """

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        raw_text = resp.text.strip()
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON from Gemini: {raw_text[:500]}")
        return parsed

    # Load existing labeled file if it exists, otherwise start from raw data
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            all_comments = json.load(f)
        print(f"Loaded {len(all_comments)} comments from {OUTPUT_PATH}")
    else:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            all_comments = json.load(f)
        print(f"Loaded {len(all_comments)} comments from {INPUT_PATH}")

    # Loop until no unlabeled comments remain
    while True:
        batch = []

        for idx, item in enumerate(all_comments):
            if "label" in item and item["label"]:
                continue

            body = item.get("body", "")
            batch.append({"idx": idx, "body": body})

            if len(batch) == BATCH_SIZE:
                break

        if not batch:
            print("\nNo unlabeled comments left — done!")
            break

        print(f"\nProcessing batch of {len(batch)} unlabeled comments starting at index {batch[0]['idx']}...")

        results = gemini_label_classifier(batch)

        for i, result in enumerate(results):
            global_index = batch[i]["idx"]
            if "label" not in all_comments[global_index] or not all_comments[global_index]["label"]:
                all_comments[global_index]["label"] = result["label"]

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(all_comments, f, indent=4, ensure_ascii=False)

        time.sleep(0.2)

    print(f"\nAll labeled comments saved to {OUTPUT_PATH}")