"""Live data layer: fetches real-time records from the CI4 public API.

Flow per question:
  classify_question()          -> which public endpoints are relevant
  fetch_relevant_portal_data() -> HTTP GET (short TTL cache) -> map to a safe
                                  allowlist -> drop expired/future items -> rank
"""
import logging
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import requests

try:  # load .env BEFORE reading any configuration below
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

log = logging.getLogger("ci4_service")

# --------------------------------------------------------------------------
# Configuration (all overridable from .env)
# --------------------------------------------------------------------------
CACHE_TTL_SECONDS = float(os.getenv("CI4_CACHE_TTL", "30"))  # 0 = always live
CONNECT_TIMEOUT = float(os.getenv("CI4_CONNECT_TIMEOUT", "3"))
READ_TIMEOUT = float(os.getenv("CI4_READ_TIMEOUT", "8"))
MAX_FIELD_CHARS = int(os.getenv("CI4_MAX_FIELD_CHARS", "400"))
MAX_RECORDS_PER_ENDPOINT = int(os.getenv("CI4_MAX_RECORDS", "200"))


def get_base_url():
    # Read at call time so a changed .env / environment is always honoured.
    return (os.getenv("CI4_API_BASE_URL") or "http://localhost:8080/api").rstrip("/")


# --------------------------------------------------------------------------
# Allowlist: output field -> candidate keys in the API response (first hit wins)
# Only these fields ever reach the LLM. Private fields (emails, user ids,
# phones, internal notes ...) are never listed, so they can never leak.
# --------------------------------------------------------------------------
FIELD_MAP = {
    "events": [
        ("title", ["title", "name"]),
        ("event_type", ["event_type", "type"]),
        ("department", ["department"]),
        ("description", ["description"]),
        ("venue", ["venue", "location"]),
        ("start_datetime", ["start_datetime", "start_date"]),
        ("end_datetime", ["end_datetime", "end_date"]),
        ("registration_deadline", ["registration_deadline"]),
    ],
    "alumni": [
        ("name", ["name", "display_name"]),  # first_name + last_name added below
        ("degree", ["degree"]),
        ("department", ["department"]),
        ("batch", ["batch_year", "batch"]),
        ("graduation_year", ["graduation_year"]),
        ("company", ["current_company", "company"]),
        ("designation", ["current_designation", "designation"]),
        ("city", ["location_city", "city"]),
        ("country", ["location_country", "country"]),
        ("skills", ["skills"]),
        ("distinguished_title", ["distinguished_title"]),
    ],
    "jobs": [
        ("title", ["job_title", "title"]),
        ("company", ["company", "company_name"]),
        ("location", ["location"]),
        ("job_type", ["job_type", "type"]),
        ("experience", ["experience", "experience_required"]),
        ("description", ["description"]),
        ("requirements", ["requirements", "eligibility"]),
        ("application_deadline", ["application_deadline", "deadline"]),
        ("apply_link", ["apply_link", "application_url"]),
    ],
    "chapters": [
        ("name", ["name", "title"]),
        ("city", ["city", "location"]),
        ("state", ["state"]),
        ("country", ["country"]),
        ("description", ["description"]),
    ],
    "stories": [
        ("title", ["title", "headline"]),
        ("summary", ["summary", "excerpt", "story", "content", "description"]),
        ("published_at", ["published_at", "created_at"]),
    ],
    "news": [
        ("title", ["title", "headline"]),
        ("summary", ["summary", "content", "description", "body"]),
        ("published_at", ["published_at", "created_at"]),
    ],
    "gallery": [
        ("title", ["title"]),
        ("category", ["category"]),
        ("description", ["description"]),
        ("event_date", ["event_date"]),
    ],
    "donations": [
        ("title", ["title", "campaign_name"]),
        ("description", ["description"]),
        ("goal_amount", ["goal_amount"]),
        ("raised_amount", ["raised_amount"]),
        ("total_donors", ["total_donors"]),
        ("deadline", ["deadline", "end_date"]),
    ],
}

# Aggregate counts the chatbot may state. Student/mentor counts are left out on
# purpose: api.md notes they are not filtered by the public-profile rules.
STATS_ALLOWED = [
    "total_alumni",
    "verified_alumni",
    "total_events",
    "total_jobs",
    "total_chapters",
    "total_stories",
    "total_news",
    "total_albums",
]

# --------------------------------------------------------------------------
# Question classification (word-boundary matching; Latin + Hindi keywords)
# --------------------------------------------------------------------------
ENDPOINT_KEYWORDS = {
    "events": ["event", "seminar", "workshop", "conference", "upcoming", "webinar",
               "reunion", "meetup", "karyakram", "कार्यक्रम", "इवेंट", "आयोजन"],
    "jobs": ["job", "opportunity", "career", "placement", "recruitment", "internship",
             "hiring", "vacancy", "naukri", "नौकरी", "रोजगार", "इंटर्नशिप"],
    "alumni": ["alumni", "alumnus", "graduate", "पूर्व छात्र", "एलुमनाई", "अलुम्नी"],
    "chapters": ["chapter", "alumni chapter", "चैप्टर"],
    "stories": ["story", "stories", "success story", "achievement", "testimonial", "सफलता की कहानी"],
    "news": ["news", "announcement", "notice", "khabar", "समाचार", "खबर", "सूचना"],
    "gallery": ["gallery", "photo", "picture", "album", "तस्वीर", "फोटो"],
    "donations": ["donation", "donate", "fundraising", "campaign", "दान"],
}

COUNT_WORDS = ["how many", "total", "number of", "count", "statistics", "stats", "kitne", "कितने"]
COUNT_ENTITIES = ["alumni", "event", "job", "chapter", "story", "stories", "news", "album", "alumnus"]

TYPO_FIXES = {"upcomming": "upcoming", "enevts": "events", "alumnis": "alumni",
              "oppurtunity": "opportunity", "oppportunities": "opportunities"}

PAST_WORDS = ["past", "previous", "old", "ended", "last year", "completed", "pichle", "पिछले"]

STOPWORDS = set("""
what when where which who whom whose how why many much tell show find give list there any the for from with and are is was
were will can could would should please about me my you your our their this that these those have has had does did not
latest recent current currently new newest update updates available open all some more also than then into out
hai hain kya kab kaun kaha kahan kitne kitna batao bataiye bataye dikhao mujhe hume humein ka ki ke ko me mein se par aur koi
kuch aap naya nayi naye aane wale wala wali kaise baare liye hoga hogi honge chahiye
""".split())


def _normalize(text):
    q = (text or "").lower()
    for wrong, right in TYPO_FIXES.items():
        q = q.replace(wrong, right)
    return q


def _has_keyword(q, keyword):
    if keyword.isascii():
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}s?(?![a-z0-9])", q) is not None
    return keyword in q  # \b does not work across Devanagari combining marks


def detect_language(text):
    if not text:
        return "english"
    if re.search(r"[\u0900-\u097F]", text):
        return "hindi"
    hinglish = {"namaste", "kaise", "hai", "hain", "aap", "kya", "kab", "kitne", "batao",
                "bataiye", "mujhe", "hume", "sabse", "kaun", "kahan", "nahi", "karo", "karna"}
    if hinglish & set(re.findall(r"[a-z]+", text.lower())):
        return "hinglish"
    return "english"


def classify_question(question):
    q = _normalize(question)
    if not q:
        return []

    # "how many alumni / total events / stats" -> aggregate counts
    asks_count = any(_has_keyword(q, w) for w in COUNT_WORDS)
    if asks_count and (any(_has_keyword(q, e) for e in COUNT_ENTITIES)
                       or _has_keyword(q, "statistics") or _has_keyword(q, "stats")):
        return ["stats"]

    matched = [name for name, words in ENDPOINT_KEYWORDS.items()
               if any(_has_keyword(q, w) for w in words)]
    # "alumni chapter" should be chapters, not the alumni directory
    if "chapters" in matched and "alumni" in matched:
        matched.remove("alumni")
    return matched or ["documents"]


# --------------------------------------------------------------------------
# HTTP fetch with short TTL cache
# --------------------------------------------------------------------------
_session = requests.Session()
_session.headers.update({"Accept": "application/json", "User-Agent": "akal-ai-assistant/1.0"})
_cache = {}
_cache_lock = threading.Lock()


def _cache_get(key):
    if CACHE_TTL_SECONDS <= 0:
        return None
    with _cache_lock:
        hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1], hit[2]
    return None


def _cache_set(key, value, fetched_at):
    if CACHE_TTL_SECONDS > 0:
        with _cache_lock:
            _cache[key] = (time.time(), value, fetched_at)


def clear_cache():
    with _cache_lock:
        _cache.clear()


def _clean_text(value):
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(v) for v in value if v not in (None, ""))
    if isinstance(value, str):
        value = re.sub(r"<[^>]+>", " ", value)          # strip HTML
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) > MAX_FIELD_CHARS:
            value = value[:MAX_FIELD_CHARS].rstrip() + "…"
    return value


def _pick(item, candidates):
    for key in candidates:
        value = item.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _map_record(endpoint, item):
    if not isinstance(item, dict):
        return {}
    record = {}
    for out_key, candidates in FIELD_MAP[endpoint]:
        value = _pick(item, candidates)
        if value is not None:
            record[out_key] = _clean_text(value)
    if endpoint == "alumni" and not record.get("name"):
        full = f"{item.get('first_name', '')} {item.get('last_name', '')}".strip()
        if full:
            record = {"name": full, **record}
    return record


def _unwrap_list(payload, endpoint):
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        for key in ("items", "records", "results", endpoint):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    return data if isinstance(data, list) else []


def _get_json(endpoint, params):
    url = f"{get_base_url()}/public/{endpoint}"
    response = _session.get(url, params=params or None, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError:
        log.warning("%s did not return JSON (got %s). CI4_API_BASE_URL probably points at a "
                    "website/frontend instead of the CI4 API.", url, response.headers.get("Content-Type"))
        raise
    if isinstance(payload, dict) and payload.get("status") is False:
        raise ValueError(payload.get("message") or "API returned status=false")
    return payload


def fetch_public_endpoint(endpoint, params=None):
    """Return (records, error, fetched_at_iso). Records are already allowlisted."""
    endpoint = endpoint.split("/")[-1]
    key = (endpoint, tuple(sorted((params or {}).items())))

    cached = _cache_get(key)
    if cached:
        return cached[0], None, cached[1]

    try:
        payload = _get_json(endpoint, params)
    except (requests.RequestException, ValueError) as exc:
        log.warning("CI4 fetch failed for %s: %s", endpoint, exc)
        return [], f"Live data for '{endpoint}' is temporarily unavailable.", None

    if endpoint == "stats":
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        counts = (data.get("counts") if isinstance(data, dict) else None) or {}
        record = {"category": "counts"}
        record.update({k: counts[k] for k in STATS_ALLOWED if k in counts})
        records = [record] if len(record) > 1 else []
    else:
        raw = _unwrap_list(payload, endpoint)[:MAX_RECORDS_PER_ENDPOINT]
        records = [r for r in (_map_record(endpoint, item) for item in raw) if r]

    fetched_at = datetime.now().isoformat(timespec="seconds")
    _cache_set(key, records, fetched_at)
    return records, None, fetched_at


# --------------------------------------------------------------------------
# Freshness filters (the backend does not filter these, see api.md)
# --------------------------------------------------------------------------
def _parse_dt(value, end_of_day=False):
    if not isinstance(value, str) or not value.strip():
        return None
    s = value.strip().replace("Z", "+00:00")
    date_only = len(s) == 10
    try:
        dt = datetime.fromisoformat(s.replace(" ", "T", 1) if "T" not in s else s)
    except ValueError:
        return None
    if dt.tzinfo:
        dt = dt.astimezone().replace(tzinfo=None)
    if date_only and end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt


def _apply_freshness(endpoint, records):
    now = datetime.now()
    if endpoint == "jobs":      # hide jobs whose application deadline has passed
        return [r for r in records
                if not (d := _parse_dt(r.get("application_deadline"), True)) or d >= now]
    if endpoint == "news":      # hide scheduled-for-future announcements
        return [r for r in records
                if not (d := _parse_dt(r.get("published_at"))) or d <= now]
    return records


# --------------------------------------------------------------------------
# Ranking
# --------------------------------------------------------------------------
def _category_words():
    words = set()
    for kws in ENDPOINT_KEYWORDS.values():
        for kw in kws:
            if kw.isascii():
                words.update(re.findall(r"[a-z0-9]+", kw))
    for w in COUNT_WORDS + COUNT_ENTITIES:
        words.update(re.findall(r"[a-z0-9]+", w))
    words.update(w + "s" for w in list(words))
    return words


_IGNORED_TERMS = STOPWORDS | _category_words() | set(PAST_WORDS) | {"event", "events", "jobs", "job"}


def _is_ignored_term(term):
    if term in _IGNORED_TERMS:
        return True
    if term.endswith("ies") and term[:-3] + "y" in _IGNORED_TERMS:   # opportunities -> opportunity
        return True
    return term.endswith("s") and term[:-1] in _IGNORED_TERMS         # jobs -> job


def _question_terms(question):
    q = _normalize(question)
    return [t for t in re.findall(r"[a-z0-9]+", q) if len(t) > 2 and not _is_ignored_term(t)]


def _record_text(record):
    return " ".join(str(v) for v in record.values() if v not in (None, "", [], {})).lower()


def _rank_records(question, records, limit):
    terms = _question_terms(question)
    if not terms:                       # "latest news", "upcoming events" -> API order
        return records[:limit] if limit else records
    scored = []
    for record in records:
        text = _record_text(record)
        score = sum(2 if re.search(rf"\b{re.escape(t)}\b", text) else (1 if t in text else 0)
                    for t in terms)
        if score:
            scored.append((score, record))
    scored.sort(key=lambda pair: pair[0], reverse=True)   # stable: keeps API order on ties
    picked = [r for _, r in scored]
    return picked[:limit] if limit else picked


# --------------------------------------------------------------------------
# Public entry point used by rag_pipeline.py
# --------------------------------------------------------------------------
def fetch_relevant_portal_data(question, limit_per_endpoint=5, targets=None):
    """Return [{'source','data','fetched_at'} | {'source','error'}]."""
    targets = targets if targets is not None else classify_question(question)
    q = _normalize(question)
    items = []

    for endpoint in targets:
        if endpoint == "documents":
            continue

        params = {}
        if endpoint == "events":
            params["filter"] = "past" if any(_has_keyword(q, w) for w in PAST_WORDS) else "upcoming"

        records, error, fetched_at = fetch_public_endpoint(endpoint, params)
        if error:
            items.append({"source": endpoint, "error": error})
            continue

        records = _apply_freshness(endpoint, records)
        chosen = records if endpoint == "stats" else _rank_records(question, records, limit_per_endpoint)
        for record in chosen:
            items.append({"source": endpoint, "data": record, "fetched_at": fetched_at})
    return items