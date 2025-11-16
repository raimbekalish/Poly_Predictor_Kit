"""
Polymarket Gamma -> Gemini AI summarizer (Not financial advice).

Behavior:
- Input: Polymarket URL / slug / numeric eventId / free text search phrase
- Fetches event + markets from Gamma API (Polymarket)
- Calls Gemini API to generate a short "AI Trade Insight (Not financial advice)"
- Prints ONLY the AI section to stdout (no raw market table).

Dependencies: ONLY Python standard library.
"""

import argparse
import datetime as dt
import json
import os
import sys
import textwrap
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# ----- Constants -----

load_dotenv()
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
USER_AGENT = "PolyPredictionKit/0.1 (hackathon-cli)"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


# ----- Errors -----

class HttpError(Exception):
    """Raised when an HTTP or JSON error occurs."""


# ----- HTTP helpers -----

def http_get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Perform a GET request and return parsed JSON."""
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        url = f"{url}?{query}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
    except Exception as e:
        raise HttpError(f"GET {url} failed: {e}") from e

    try:
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        raise HttpError(f"Failed to decode JSON from {url}: {e}") from e


def http_post_json(
    url: str,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    """Perform a POST request with JSON body and return parsed JSON."""
    payload = json.dumps(body).encode("utf-8")

    all_headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if headers:
        all_headers.update(headers)

    req = urllib.request.Request(
        url,
        data=payload,
        headers=all_headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        raise HttpError(f"POST {url} failed: {e}") from e

    try:
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        raise HttpError(f"Failed to decode JSON from {url}: {e}") from e


# ----- Gamma / Polymarket helpers -----

def extract_slug_from_url(url: str) -> Optional[str]:
    """
    Extract Polymarket slug from URL.

    Example:
        https://polymarket.com/event/fed-decision-in-october?tid=123
        -> "fed-decision-in-october"
    """
    try:
        parsed = urllib.parse.urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            return None

        for i, part in enumerate(parts):
            if part in ("event", "market") and i + 1 < len(parts):
                return parts[i + 1]

        # Fallback: last path segment
        return parts[-1] if parts else None
    except Exception:
        return None


def get_event_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get event by slug using:
        GET /events/slug/{slug}
    """
    slug_enc = urllib.parse.quote(slug, safe="")
    url = f"{GAMMA_BASE_URL}/events/slug/{slug_enc}"
    try:
        event = http_get_json(url)
    except HttpError:
        return None
    if isinstance(event, dict) and event.get("id"):
        return event
    return None


def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Get event by id using:
        GET /events/{id}
    """
    id_enc = urllib.parse.quote(event_id, safe="")
    url = f"{GAMMA_BASE_URL}/events/{id_enc}"
    try:
        event = http_get_json(url)
    except HttpError:
        return None
    if isinstance(event, dict) and event.get("id"):
        return event
    return None


def search_event(query: str) -> Optional[Dict[str, Any]]:
    """
    Search events using:
        GET /public-search?q=<query>

    We take the first event from "events" array.
    """
    params = {
        "q": query,
        "limit_per_type": 5,
        "search_profiles": "false",
        "search_tags": "false",
    }
    payload = http_get_json(f"{GAMMA_BASE_URL}/public-search", params=params)

    events = payload.get("events") if isinstance(payload, dict) else None
    if isinstance(events, list) and events:
        return events[0]
    return None


def classify_input(raw: str) -> Tuple[str, str]:
    """
    Classify the user input.

    Returns:
        (mode, value)
        mode ∈ {"url", "id", "slug", "search"}
    """
    s = raw.strip()

    # URL
    if s.startswith("http://") or s.startswith("https://"):
        return "url", s

    # numeric eventId
    if s.isdigit():
        return "id", s

    # slug-like: no spaces, contains dash
    if " " not in s and "-" in s:
        return "slug", s

    # everything else -> search phrase
    return "search", s


def load_event_from_query(raw_query: str) -> Dict[str, Any]:
    """
    Main resolver: from user input to a single Gamma event object.

    Strategy:
    - URL -> slug -> event-by-slug -> fallback search
    - numeric -> event-by-id -> fallback search
    - slug   -> event-by-slug -> fallback search
    - search -> search only
    """
    mode, value = classify_input(raw_query)

    if mode == "url":
        slug = extract_slug_from_url(value)
        if slug:
            ev = get_event_by_slug(slug)
            if ev:
                return ev
        ev = search_event(value)
        if ev:
            return ev
        raise RuntimeError("Could not find event by URL (slug + search failed).")

    if mode == "id":
        ev = get_event_by_id(value)
        if ev:
            return ev
        ev = search_event(value)
        if ev:
            return ev
        raise RuntimeError("Could not find event by id (id + search failed).")

    if mode == "slug":
        ev = get_event_by_slug(value)
        if ev:
            return ev
        ev = search_event(value)
        if ev:
            return ev
        raise RuntimeError("Could not find event by slug (slug + search failed).")

    # mode == "search"
    ev = search_event(value)
    if ev:
        return ev
    raise RuntimeError("Search returned no matching events.")


# ----- Formatting helpers -----

def parse_iso_datetime(s: Optional[str]) -> Optional[dt.datetime]:
    """Parse ISO-8601 datetime with optional Z suffix."""
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def format_dt_human(d: Optional[dt.datetime]) -> str:
    """Format datetime in UTC as human-readable string."""
    if d is None:
        return "N/A"
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    d_utc = d.astimezone(dt.timezone.utc)
    return d_utc.strftime("%Y-%m-%d %H:%M UTC")


def to_float(value: Any) -> Optional[float]:
    """Safely convert different value types to float or return None."""
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return None
    try:
        return float(str(value))
    except Exception:
        return None


def format_usdc(value: Any) -> str:
    """Format a numeric USD/USDC value in a friendly way."""
    f = to_float(value)
    if f is None:
        return "N/A"
    if abs(f) >= 1000:
        return f"${f:,.0f}"
    return f"${f:,.2f}"


def parse_outcomes_and_prices(market: Dict[str, Any]) -> List[Tuple[str, Optional[float]]]:
    """
    Parse outcomes and outcomePrices from a market object.

    Gamma usually stores them as JSON strings:
        outcomes:       '["Yes","No"]'
        outcomePrices:  '["0.54","0.46"]'
    """

    raw_outcomes = market.get("outcomes") or ""
    raw_prices = market.get("outcomePrices") or ""

    def parse_list(raw: str) -> List[str]:
        if not raw:
            return []
        # Try JSON first
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            pass
        # Fallback: comma-separated string
        return [item.strip() for item in raw.split(",") if item.strip()]

    outcomes = parse_list(raw_outcomes)
    price_strs = parse_list(raw_prices)

    result: List[Tuple[str, Optional[float]]] = []
    for i, name in enumerate(outcomes):
        price: Optional[float] = None
        if i < len(price_strs):
            price = to_float(price_strs[i])
        result.append((name, price))
    return result


def get_event_status(event: Dict[str, Any]) -> str:
    """Return a simple status string for the event."""
    closed = event.get("closed")
    active = event.get("active")
    if closed:
        return "CLOSED"
    if active:
        return "OPEN"
    return "UNKNOWN"


def select_markets_for_ai(event: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Select up to `limit` markets for AI summary.

    Priority: open markets first, then closed ones.
    """
    markets = event.get("markets") or []
    if not isinstance(markets, list):
        return []

    open_markets = [m for m in markets if not m.get("closed")]
    closed_markets = [m for m in markets if m.get("closed")]
    ordered = open_markets + closed_markets
    return ordered[:limit]


# ----- Gemini helpers -----

def get_gemini_api_key() -> Optional[str]:
    """Read Gemini API key from environment."""
    return os.environ.get("GEMINI_API_KEY")


def build_gemini_prompt(event: Dict[str, Any], markets: List[Dict[str, Any]]) -> str:
    """Construct a text prompt summarizing the event for Gemini."""
    title = event.get("title") or "<no title>"
    slug = event.get("slug") or "N/A"
    status = get_event_status(event)
    end_dt = parse_iso_datetime(event.get("endDate"))
    end_str = format_dt_human(end_dt)
    event_vol = format_usdc(event.get("volume"))

    lines: List[str] = []
    lines.append(f"Event title: {title}")
    lines.append(f"Event slug: {slug}")
    lines.append(f"Event status: {status}")
    lines.append(f"Event end date (UTC): {end_str}")
    lines.append(f"Event volume (USDC): {event_vol}")
    lines.append("")
    lines.append("Markets summary:")

    for idx, m in enumerate(markets[:3], start=1):
        q = m.get("question") or "<no question>"
        m_closed = m.get("closed")
        m_status = "CLOSED" if m_closed else "OPEN"
        m_vol = format_usdc(m.get("volume"))
        lines.append(f"{idx}. Question: {q}")
        lines.append(f"   Status: {m_status}, Volume: {m_vol}")

        outcomes = parse_outcomes_and_prices(m)
        if outcomes:
            out_parts: List[str] = []
            for name, price in outcomes:
                if price is None:
                    out_parts.append(f"{name}: N/A")
                else:
                    prob = price * 100.0
                    out_parts.append(f"{name}: {price:.2f} (~{prob:.1f}%)")
            lines.append("   Outcomes: " + "; ".join(out_parts))
        lines.append("")

    if not markets:
        lines.append("No markets were found for this event.")

    summary = "\n".join(lines)

    prompt = f"""
You are an AI assistant helping a user think about prediction markets on Polymarket.

Here is structured data about one Polymarket event and some of its markets:

{summary}

Using this information, write a short AI Trade Insight section in 3–6 sentences.

Focus on:
- What current prices roughly imply about market expectations.
- 1–2 key scenarios or risk factors that could change the odds.
- A balanced view that mentions both upside and downside perspectives.

Rules:
- Do NOT give explicit instructions like "you should buy" or "sell now".
- Do NOT mention specific position sizes.
- Explicitly remind the reader that this is NOT financial advice.

Respond with plain text only (no bullet points, no markdown headings).
""".strip()
    return prompt


def call_gemini_insight(prompt: str, api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> str:
    """
    Call Gemini text model through the public generateContent REST API.
    """
    model_escaped = urllib.parse.quote(model, safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_escaped}:generateContent"

    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    headers = {
        "x-goog-api-key": api_key,
    }

    resp = http_post_json(url, body, headers=headers)

    # Parse standard Gemini response:
    #   candidates[0].content.parts[*].text
    try:
        candidates = resp.get("candidates") or []
        if not candidates:
            return "Gemini did not return any candidates."
        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        texts = [
            p.get("text", "")
            for p in parts
            if isinstance(p, dict) and "text" in p
        ]
        text = "\n".join(t for t in texts if t).strip()
        return text or "Gemini returned an empty response."
    except Exception as e:
        return f"Failed to parse Gemini response: {e}"


# ----- Main CLI -----

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Polymarket Gamma -> Gemini AI Trade Insight (Not financial advice)."
    )
    parser.add_argument(
        "query",
        help="Polymarket URL, slug, numeric event ID, or free-text search phrase.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_GEMINI_MODEL,
        help=f"Gemini model id (default: {DEFAULT_GEMINI_MODEL}).",
    )

    args = parser.parse_args(argv)

    # Step 1: Fetch event from Gamma
    try:
        event = load_event_from_query(args.query)
    except HttpError as e:
        print(f"[ERROR] Network/API error while talking to Gamma API:\n{e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    # Step 2: Select markets (for AI only, no printing)
    markets = select_markets_for_ai(event)

    # Step 3: Prepare Gemini
    api_key = get_gemini_api_key()
    if not api_key:
        print("[AI] GEMINI_API_KEY is not set. Unable to generate AI Trade Insight.", file=sys.stderr)
        return 1

    print("-" * 88)
    print("AI Trade Insight (Not financial advice):")

    try:
        prompt = build_gemini_prompt(event, markets)
        insight = call_gemini_insight(prompt, api_key, model=args.model)
    except HttpError as e:
        insight = f"Gemini API request failed: {e}"
    except Exception as e:
        insight = f"Unexpected error while talking to Gemini: {e}"

    wrapped = textwrap.fill(insight, width=88)
    print(wrapped)
    print("-" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
