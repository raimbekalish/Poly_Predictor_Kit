from flask import Flask, request, jsonify
from flask_cors import CORS

from poly_event_ai_summarizer import generate_insight_from_query, HttpError

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/ai-insight", methods=["POST"])
def ai_insight():
    data = request.get_json() or {}
    slug = data.get("slug")

    if not slug:
        return jsonify({"error": "Missing slug"}), 400

    try:
        # We pass slug directly; the summarizer resolves slug/URL/search internally
        insight = generate_insight_from_query(slug)
        return jsonify({"insight": insight})
    except HttpError as e:
        return jsonify({"error": f"Gamma/Gemini HTTP error: {e}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("AI Insight API running on http://127.0.0.1:5002")
    app.run(port=5002, debug=True)