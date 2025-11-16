import joblib
    
    
model = joblib.load("comment_classifier.pkl")
print(model.predict(["Hi"]))

# WIP