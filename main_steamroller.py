from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timezone
import math
import json

# ---------- Config ----------

GAMMA_BASE_URL = "https://gamma-api.polymarket.com"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# ---------- Helper functions ----------

def parse_iso_datetime(s: str) -> datetime | None:
    """Turn '2025-10-31T23:59:00Z' into a timezone-aware datetime."""
    if not s:
        return None
    try:
        # Gamma uses Z for UTC, Python wants +00:00
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def safe_outcome_list(value):
    """
    Gamma docs show outcomes / outcomePrices as <string>, but in practice
    they are usually arrays. This helper tries to handle both cases.
    """
    if value is None:
        return []

    # Already a list?
    if isinstance(value, list):
        return value

    # Sometimes a JSON-encoded string
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            # Not JSON, maybe comma-separated
            parts = [p.strip() for p in value.split(",")]
            return [p for p in parts if p]

    # Fallback: wrap single value
    return [value]


def compute_outcome_metrics(probability: float, now: datetime, end_dt: datetime | None):
    """
    Given p in [0,1], compute:
    - max gain / loss per 1$
    - wipeout factor
    - simple risk labels
    """
    EPS = 1e-4
    p_raw = probability
    p = max(EPS, min(1.0 - EPS, p_raw))

    max_gain = 1.0 - p
    max_loss = p

    wipeout_factor = max_loss / max_gain

    if p < 0.75:
        risk_label = "low"
    elif p < 0.9:
        risk_label = "medium"
    else:
        risk_label = "high" if wipeout_factor >= 10.0 else "medium"

    days_left = None
    time_risk = "unknown"
    if end_dt is not None:
        end_naive = end_dt.replace(tzinfo=None)
        now_naive = now.replace(tzinfo=None)

        delta_days = (end_naive - now_naive).total_seconds() / 86400.0
        if delta_days < 0:
            delta_days = 0.0
        days_left = delta_days

        if days_left == 0:
            time_risk = "low"
        elif p > 0.9 and days_left > 7:
            time_risk = "high"
        elif p > 0.85 and days_left > 3:
            time_risk = "medium"
        else:
            time_risk = "low"

    return {
        "probability": p,
        "max_gain_per_1": max_gain,
        "max_loss_per_1": max_loss,
        "wipeout_factor": wipeout_factor,
        "risk_label": risk_label,
        "time_risk": time_risk,
        "days_left": days_left,
    }


def pick_steamroller_side(outcome_metrics: dict):
    """
    outcome_metrics: dict like {"YES": {...}, "NO": {...}}
    Decide which side is the "steamroller" (if any).
    """
    best_side = None
    best_score = -1.0

    for name, m in outcome_metrics.items():
        p = m["probability"]
        wipe = m["wipeout_factor"]
        time_risk = m["time_risk"]
        days_left = m.get("days_left") or 0.0

        if wipe is None:
            continue

        if p < 0.9 or wipe < 10.0:
            continue

        score = wipe * p

        if time_risk == "high":
            score *= 1.3
        elif time_risk == "medium":
            score *= 1.1

        if score > best_score:
            best_score = score
            best_side = name

    if best_side is None:
        return {
            "steamroller_side": None,
            "overall_risk": "low",
            "human_message": "No clear steamroller pattern: no side looks like 'tiny upside vs huge downside'.",
        }

    m = outcome_metrics[best_side]
    p = m["probability"]
    wipe = m["wipeout_factor"]
    days_left = m["days_left"]

    wipe_int = int(math.floor(wipe)) if wipe is not None else None

    if best_score > 30:
        overall = "high"
    elif best_score > 15:
        overall = "medium"
    else:
        overall = "low"

    parts = []
    parts.append(f"{best_side} looks like a steamroller trade.")
    parts.append(f"Current implied probability is about {p * 100:.1f}%.")

    if wipe_int and wipe_int > 1:
        parts.append(f"At this price, one loss wipes roughly {wipe_int} average wins.")
    if days_left is not None:
        parts.append(f"There are about {days_left:.1f} days left until resolution.")

    msg = " ".join(parts)

    return {
        "steamroller_side": best_side,
        "overall_risk": overall,
        "human_message": msg,
    }


# ---------- Main endpoint ----------

@app.route("/api/steamroller", methods=["GET"])
def steamroller():
    slug = request.args.get("slug")
    if not slug:
        return jsonify({"error": "missing ?slug= parameter"}), 400

    try:
        resp = requests.get(f"{GAMMA_BASE_URL}/events/slug/{slug}", timeout=5)
    except Exception as e:
        return jsonify({"error": "failed_to_call_gamma", "details": str(e)}), 502

    if resp.status_code != 200:
        return jsonify({
            "error": "gamma_returned_non_200",
            "status_code": resp.status_code,
            "body": resp.text,
        }), 502

    event = resp.json()
    markets = event.get("markets") or []
    active_markets = [m for m in markets if m.get("active") and not m.get("closed")]

    if active_markets:
        market = active_markets[0]
    else:
        market = markets[0]

    question = market.get("question") or market.get("title") or slug
    end_iso = market.get("endDateIso") or market.get("endDate")
    end_dt = parse_iso_datetime(end_iso)
    now = datetime.now(timezone.utc)

    outcomes_raw = safe_outcome_list(market.get("outcomes"))
    prices_raw = safe_outcome_list(market.get("outcomePrices"))

    if not outcomes_raw or not prices_raw or len(outcomes_raw) != len(prices_raw):
        return jsonify({
            "slug": slug,
            "market_title": question,
            "error": "could_not_parse_outcomes_or_prices",
            "raw_outcomes": outcomes_raw,
            "raw_prices": prices_raw,
        }), 500

    outcome_metrics = {}
    for outcome_name, price_value in zip(outcomes_raw, prices_raw):
        try:
            p = float(price_value)
            if p > 1.0:
                p = p / 100.0
        except Exception:
            continue

        metrics = compute_outcome_metrics(p, now, end_dt)
        outcome_metrics[str(outcome_name)] = metrics

    if not outcome_metrics:
        return jsonify({
            "slug": slug,
            "market_title": question,
            "error": "no_valid_outcomes_after_parsing",
        }), 500

    summary = pick_steamroller_side(outcome_metrics)

    any_outcome = next(iter(outcome_metrics.values()))
    response = {
        "slug": slug,
        "market_title": question,
        "end_time": end_iso,
        "days_left": any_outcome["days_left"],
        "outcomes": outcome_metrics,
        "steamroller_summary": summary,
    }
    return jsonify(response)


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)