from commentsReceiver import getComments
from geminiAutoLabelAssigner import geminiAutoClassifier
from upload_to_snowflake import upload_training_data
from train_model_snowflake import train_model

poly_event_link = input("Polymarket event link: ")

getComments(poly_event_link)

geminiAutoClassifier()

upload_training_data()

train_model()
