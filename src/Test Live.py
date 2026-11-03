"""Run this against your REAL CI4 API to see exactly what the chatbot will fetch.

    cd src
    python test_live_api.py
    python test_live_api.py "Which jobs are open right now?"
"""
import json
import sys

from ci4_service import classify_question, fetch_relevant_portal_data, get_base_url

SAMPLES = [
    "What are the upcoming events?",
    "Any job opportunities?",
    "Tell me the latest news",
    "How many alumni are there?",
    "List alumni chapters",
]

questions = sys.argv[1:] or SAMPLES
print("CI4 base URL:", get_base_url())

# Probe: does this URL really serve the CI4 JSON API?
import requests

probe = f"{get_base_url()}/public/stats"
try:
    r = requests.get(probe, timeout=5)
    kind = r.headers.get("Content-Type", "")
    if "json" in kind:
        print(f"OK   {probe} -> JSON (HTTP {r.status_code})")
    else:
        print(f"BAD  {probe} -> {kind or 'unknown'} (HTTP {r.status_code}). This is a web page, not the API.")
        print("     Point CI4_API_BASE_URL at the CI4 backend, e.g. http://localhost:8080/api")
except requests.RequestException as exc:
    print(f"BAD  cannot reach {probe}: {exc}")
for q in questions:
    print("\n" + "=" * 70)
    print("Q:", q)
    print("Endpoints:", classify_question(q))
    items = fetch_relevant_portal_data(q)
    if not items:
        print("  (no live records matched)")
    for item in items:
        print(" ", json.dumps(item, ensure_ascii=False, default=str))