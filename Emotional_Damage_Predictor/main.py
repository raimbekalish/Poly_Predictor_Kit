import joblib
import json
import math
from commentsReceiver import getComments
from upload_to_snowflake import upload_training_data
from train_model_snowflake import train_model
    
INPUT_PATH = "./data.json"
OUTPUT_PATH = "./data_labeled.json"
poly_event_link = "https://polymarket.com/event/monad-market-cap-fdv-one-day-after-launch?tid=1763315191827"
# input("Please, provide a Polymarket Event link: ")
getComments(poly_event_link)

with open(INPUT_PATH, "r", encoding="utf-8") as f:
       all_comments = json.load(f)

model = joblib.load("comment_classifier.pkl")
emotional_rate = 0
rational_rate = 0

for item in all_comments:
    if "label" in item and item["label"]:
           continue
    else:
            item["label"] = model.predict([item["body"]])[0]

            if item["label"] == "EMOTIONAL":
                    emotional_rate += 1
            elif item["label"] == "RATIONAL":
                    rational_rate += 1
            else:
                    continue      

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
       json.dump(all_comments, f, indent=4)

upload_training_data()
train_model()

print("Emotional Damage rate results:")
final_rate = (emotional_rate + rational_rate) % 100
emotional_percent = (emotional_rate / final_rate) * 100
rational_percent = (rational_rate / final_rate) * 100

if emotional_percent > rational_percent:
       print(f"From comments provided it seems like the event might be based on Emotions: {math.ceil(emotional_percent)}%")
elif rational_percent > emotional_percent:
       print(f"From comments provided it seems like the event might be based on Rationalism: {math.ceil(rational_percent)}%")
else: 
        print(f"From comments provided it seems like the event is equally Emotional and Rational")