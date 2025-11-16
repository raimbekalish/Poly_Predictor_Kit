import json
import os
from dotenv import load_dotenv
import pandas as pd
from snowflake.snowpark import Session


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_LABELED_PATH = os.path.join(BASE_DIR, "data_labeled.json")

def upload_training_data():
    load_dotenv()

    connection_parameters = {
        "account":   os.getenv("SNOW_ACCOUNT"),
        "user":      os.getenv("SNOW_USER"),
        "password":  os.getenv("SNOW_PASSWORD"),
        "role":      os.getenv("SNOW_ROLE"),
        "warehouse": os.getenv("SNOW_WAREHOUSE"),
        "database":  os.getenv("SNOW_DATABASE"),
        "schema":    os.getenv("SNOW_SCHEMA"),
    }
    
    if not os.path.exists(DATA_LABELED_PATH):
        raise FileNotFoundError(f"Missing labeled file: {DATA_LABELED_PATH}")

    with open(DATA_LABELED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)[["body", "label"]]
    df.columns = ["BODY", "LABEL"]
    session = Session.builder.configs(connection_parameters).create()

    session.write_pandas(
        df,
        table_name="COMMENT_LABELS_DATA",
        auto_create_table=False,
        overwrite=False
    )

    print(f"Successfully uploaded {len(df)} rows to Snowflake COMMENT_LABELS_DATA table")