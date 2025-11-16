import json
import os
from dotenv import load_dotenv
import pandas as pd
from snowflake.snowpark import Session

    
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


    with open("data_labeled.json", "r") as f:
        data = json.load(f)

    df = pd.DataFrame(data)[["body", "label"]]
    df.columns = ["BODY", "LABEL"]

    # connect to snowflake
    session = Session.builder.configs(connection_parameters).create()

    # create table
    # session.sql("""
    #     CREATE OR REPLACE TABLE COMMENT_LABELS_DATA (
    #                 BODY STRING,
    #                 LABEL STRING
    #     )
    # """).collect()
    
    # upload data
    session.write_pandas(
        df,
        table_name="COMMENT_LABELS_DATA",
        auto_create_table=False,
        overwrite=False
    )

    print(f"Successfully uploaded {len(df)} rows to Snowflake data table")
