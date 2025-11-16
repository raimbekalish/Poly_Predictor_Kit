import os
from dotenv import load_dotenv
from snowflake.snowpark import Session
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import joblib

def train_model():

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

    # initializing session connection with snowflake
    session = Session.builder.configs(connection_parameters).create()

    # read and get the data training table
    sf_df = session.table("COMMENT_LABELS_DATA")

    # bring data table to local memory
    pdf = sf_df.to_pandas()

    print(f"Successfully loaded {len(pdf)} comments from SnowFlake")

    x = pdf["BODY"]
    y = pdf["LABEL"]

    # Splitting into train (80%) and test (20%) sets
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        stratify=y, # keeps proportions balanced between train/test
        random_state=42
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])

    print("Training process started...")
    model.fit(x_train, y_train)

    print("Test process started...")
    y_pred = model.predict(x_test)

    report = classification_report(y_test, y_pred)
    print("\nTest Results:\n")
    print(report)

    # Save trained modal
    joblib.dump(model, "comment_classifier.pkl")
    print("\nSaved trained model.")

