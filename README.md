🚀 Poly Predictor Kit

AI-powered toolkit that analyzes Polymarket markets using real-time data, sentiment classification, and Gemini 2.5 Flash insights.
Includes a Chrome extension, a sentiment ML pipeline, and a Python AI Insight CLI.

⭐ Features
🔮 AI Trade Insight (Not financial advice)

A Python CLI tool that:

Accepts Polymarket URLs / slugs / IDs / search phrases

Fetches event + market data via Polymarket Gamma API

Generates a short insight using Gemini 2.5 Flash

Outputs clean text suitable for terminals or backend services

Run:

export GEMINI_API_KEY="your-key"
python poly_event_ai_summarizer.py "https://polymarket.com/event/some-event"

😡 Emotional Damage Predictor (Sentiment ML)

A complete pipeline that:

Collects Polymarket comments

Uses Gemini to auto-label comments: EMOTIONAL, RATIONAL, SPAM

Uploads the dataset to Snowflake

Trains a logistic regression classifier (comment_classifier.pkl)

Powers the backend sentiment scoring

Modules live in:

Emotional_Damage_Predictor/

🧩 Chrome Extension — Polymarket Copilot

A Manifest V3 extension that overlays a floating card on any Polymarket event page.
It retrieves:

Sentiment score

Emotional bias label

AI Trade Insight

Structure:

extension/
  manifest.json
  content.js


Load manually via chrome://extensions → Load unpacked.

🏛️ Project Structure
Poly_Predictor_Kit/
│
├── extension/                    # Chrome extension (UI layer)
│   ├── manifest.json
│   └── content.js
│
├── Emotional_Damage_Predictor/   # ML + Snowflake data pipeline
│   ├── commentsReceiver.py
│   ├── geminiAutoLabelAssigner.py
│   ├── upload_to_snowflake.py
│   ├── train_model_snowflake.py
│   ├── training_data_expansion.py
│   └── main.py
│
├── poly_event_ai_summarizer.py   # Gemini-powered market insight CLI
├── .gitignore
└── README.md

🔧 Installation & Usage
1. AI Insight CLI
export GEMINI_API_KEY="your-key"
python poly_event_ai_summarizer.py "super-tuesday-results"


Works with:

Full URLs

Event IDs

Slugs

Search phrases

2. Sentiment Model Pipeline
python Emotional_Damage_Predictor/commentsReceiver.py
python Emotional_Damage_Predictor/geminiAutoLabelAssigner.py
python Emotional_Damage_Predictor/upload_to_snowflake.py
python Emotional_Damage_Predictor/train_model_snowflake.py

3. Chrome Extension

Go to chrome://extensions

Enable Developer mode

Load the extension/ folder

🧠 Technologies Used

Gemini 2.5 Flash — generative insights & auto-labeling

Polymarket Gamma API — market + event data

Snowflake (Snowpark) — scalable dataset storage & processing

scikit-learn — sentiment classification model

Chrome Extensions (Manifest V3) — frontend integration

Python (standard library) — no external libs required for the CLI

🧩 Backend Response Format

Chrome extension expects:

{
  "score": "0.74",
  "label": "Emotional Sentiment",
  "explanation": "Current odds suggest that... (Not financial advice)"
}
