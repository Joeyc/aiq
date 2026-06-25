#!/usr/bin/env python3
"""
AI Cheatsheet Auto-Updater
--------------------------
Queries Anthropic models API, OpenAI models API, and
web-searchable release notes to produce ai_data.json.
The cheatsheet HTML reads this JSON on load.

Usage:
  python update_data.py                  # run once
  python update_data.py --dry-run        # print without saving

Schedule via cron (weekly):
  0 9 * * 1 cd /path/to/cheatsheet && python update_data.py >> update.log 2>&1

Or GitHub Actions (see .github/workflows/update.yml)
"""

import os, sys, json, re, datetime, urllib.request, urllib.error, argparse

DRY_RUN = "--dry-run" in sys.argv
OUTPUT   = "ai_data.json"

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY", "")

NOW = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# ── helpers ───────────────────────────────────────────────────────────────────

def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [WARN] {url} -> {e}")
        return None

def fetch_text(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {
        "User-Agent": "cheatsheet-updater/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode(errors="ignore")
    except Exception as e:
        print(f"  [WARN] {url} -> {e}")
        return ""


# ── Anthropic models ──────────────────────────────────────────────────────────

ANTHROPIC_TIER_MAP = {
    "haiku":  {"tier": "Fast / cheap",    "tier_class": "tier-haiku"},
    "sonnet": {"tier": "Balanced",        "tier_class": "tier-sonnet"},
    "opus":   {"tier": "Most capable",    "tier_class": "tier-opus"},
    "fable":  {"tier": "Frontier",        "tier_class": "tier-opus"},
    "mythos": {"tier": "Research preview","tier_class": "tier-opus"},
}

ANTHROPIC_CONTEXT_MAP = {
    "haiku":  "200k",
    "sonnet": "1M",
    "opus":   "1M",
    "fable":  "1M",
    "mythos": "1M",
}

ANTHROPIC_STRENGTH_MAP = {
    "haiku":  "High-volume, low-latency tasks",
    "sonnet": "Best all-round model for most tasks",
    "opus":   "Complex reasoning, agentic coding",
    "fable":  "Frontier reasoning and multimodal tasks",
    "mythos": "Defensive cybersecurity (research preview)",
}

def get_tier_key(model_id):
    for key in ANTHROPIC_TIER_MAP:
        if key in model_id.lower():
            return key
    return "sonnet"

def fetch_anthropic_models():
    print("Fetching Anthropic models...")
    if not ANTHROPIC_KEY:
        print("  [WARN] ANTHROPIC_API_KEY not set — using fallback data")
        return get_anthropic_fallback()

    data = fetch_json(
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01"
        }
    )
    if not data or "data" not in data:
        print("  [WARN] Could not fetch Anthropic models — using fallback")
        return get_anthropic_fallback()

    models = []
    seen   = set()

    for m in data["data"]:
        mid = m.get("id", "")
        # skip dated snapshots if we already have the base
        base = re.sub(r"-\d{8}$", "", mid)
        if base in seen:
            continue
        seen.add(base)

        # skip deprecated / retired unless nothing else available
        if any(x in mid for x in ["claude-1", "claude-2", "claude-instant",
                                    "claude-3-", "2024"]):
            continue

        tier_key = get_tier_key(mid)
        tier_info = ANTHROPIC_TIER_MAP[tier_key]
        models.append({
            "lab":        "Anthropic",
            "model_id":   mid,
            "tier":       tier_info["tier"],
            "tier_class": tier_info["tier_class"],
            "context":    ANTHROPIC_CONTEXT_MAP.get(tier_key, "200k"),
            "strength":   ANTHROPIC_STRENGTH_MAP.get(tier_key, "General purpose"),
            "input_price": None,  # not in API — see pricing note
        })

    if not models:
        return get_anthropic_fallback()

    print(f"  Found {len(models)} Anthropic models")
    return models

def get_anthropic_fallback():
    """Curated fallback when API key is absent or request fails."""
    return [
        {"lab":"Anthropic","model_id":"claude-haiku-4-5",  "tier":"Fast / cheap",  "tier_class":"tier-haiku",  "context":"200k","strength":"High-volume, low-latency tasks",       "input_price":"$0.80"},
        {"lab":"Anthropic","model_id":"claude-sonnet-4-6", "tier":"Balanced",       "tier_class":"tier-sonnet", "context":"1M",  "strength":"Best all-round model for most tasks",  "input_price":"$3.00"},
        {"lab":"Anthropic","model_id":"claude-opus-4-6",   "tier":"Most capable",   "tier_class":"tier-opus",   "context":"1M",  "strength":"Complex reasoning, agentic coding",    "input_price":"$15.00"},
        {"lab":"Anthropic","model_id":"claude-opus-4-8",   "tier":"Most capable",   "tier_class":"tier-opus",   "context":"1M",  "strength":"Hardest reasoning, agentic coding",    "input_price":"$15.00"},
    ]


# ── OpenAI models ─────────────────────────────────────────────────────────────

OPENAI_INCLUDE = ["gpt-4o", "o1", "o3", "o4", "gpt-4-turbo"]
OPENAI_SKIP    = ["realtime", "audio", "preview", "instruct", "vision",
                   "embedding", "dall-e", "whisper", "tts", "babbage",
                   "davinci", "curie", "ada"]

OPENAI_META = {
    "gpt-4o":       {"tier":"Balanced","tier_class":"tier-sonnet","context":"128k","strength":"Multimodal (text, image, audio, vision)","input_price":"$2.50"},
    "gpt-4o-mini":  {"tier":"Fast / cheap","tier_class":"tier-haiku","context":"128k","strength":"Cost-efficient everyday tasks","input_price":"$0.15"},
    "o3":           {"tier":"Reasoning","tier_class":"tier-opus","context":"200k","strength":"Step-by-step reasoning, maths, science","input_price":"$10.00"},
    "o4-mini":      {"tier":"Reasoning","tier_class":"tier-sonnet","context":"200k","strength":"Fast reasoning at lower cost","input_price":"$1.10"},
    "o1":           {"tier":"Reasoning","tier_class":"tier-opus","context":"200k","strength":"Deep reasoning, complex problems","input_price":"$15.00"},
}

def fetch_openai_models():
    print("Fetching OpenAI models...")
    if not OPENAI_KEY:
        print("  [WARN] OPENAI_API_KEY not set — using fallback data")
        return get_openai_fallback()

    data = fetch_json(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {OPENAI_KEY}"}
    )
    if not data or "data" not in data:
        print("  [WARN] Could not fetch OpenAI models — using fallback")
        return get_openai_fallback()

    models = []
    seen   = set()

    for m in sorted(data["data"], key=lambda x: x.get("created", 0), reverse=True):
        mid = m.get("id", "")
        if any(skip in mid for skip in OPENAI_SKIP):
            continue
        if not any(inc in mid for inc in OPENAI_INCLUDE):
            continue

        # deduplicate by base name
        base = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", mid)
        if base in seen:
            continue
        seen.add(base)

        meta = OPENAI_META.get(base, OPENAI_META.get(mid, {
            "tier": "General purpose",
            "tier_class": "tier-sonnet",
            "context": "128k",
            "strength": "General purpose OpenAI model",
            "input_price": "—"
        }))

        models.append({
            "lab":        "OpenAI",
            "model_id":   mid,
            **meta,
        })

    if not models:
        return get_openai_fallback()

    print(f"  Found {len(models)} OpenAI models")
    return models

def get_openai_fallback():
    return [
        {"lab":"OpenAI","model_id":"gpt-4o",      "tier":"Balanced",     "tier_class":"tier-sonnet","context":"128k","strength":"Multimodal (text, image, audio, vision)", "input_price":"$2.50"},
        {"lab":"OpenAI","model_id":"gpt-4o-mini",  "tier":"Fast / cheap", "tier_class":"tier-haiku", "context":"128k","strength":"Cost-efficient everyday tasks",          "input_price":"$0.15"},
        {"lab":"OpenAI","model_id":"o3",            "tier":"Reasoning",    "tier_class":"tier-opus",  "context":"200k","strength":"Step-by-step reasoning, maths, science","input_price":"$10.00"},
        {"lab":"OpenAI","model_id":"o4-mini",       "tier":"Reasoning",    "tier_class":"tier-sonnet","context":"200k","strength":"Fast reasoning at lower cost",           "input_price":"$1.10"},
    ]


# ── Other providers (curated, updated manually or via web fetch) ───────────────

def get_other_models():
    """
    Google, Meta, Mistral, xAI — not queryable via open API.
    Curated here; update when new models release.
    """
    return [
        {"lab":"Google",  "model_id":"gemini-2.0-flash",    "tier":"Fast",         "tier_class":"tier-haiku",  "context":"1M",  "strength":"Speed + very large context at low cost",      "input_price":"$0.10"},
        {"lab":"Google",  "model_id":"gemini-1.5-pro",      "tier":"Balanced",     "tier_class":"tier-sonnet", "context":"2M",  "strength":"Largest context window of any major model",   "input_price":"$1.25"},
        {"lab":"Meta",    "model_id":"llama-3.1-405b",       "tier":"Capable",      "tier_class":"tier-opus",   "context":"128k","strength":"Open source — self-host, no API fees",        "input_price":"Free (self-host)"},
        {"lab":"Mistral", "model_id":"mistral-large-2",      "tier":"Balanced",     "tier_class":"tier-sonnet", "context":"128k","strength":"Strong multilingual, EU data residency",      "input_price":"$2.00"},
        {"lab":"xAI",     "model_id":"grok-3",               "tier":"Balanced",     "tier_class":"tier-sonnet", "context":"131k","strength":"Real-time X/Twitter data access",             "input_price":"$3.00"},
    ]


# ── Announcements via web search (Claude API) ─────────────────────────────────

ANNOUNCEMENT_SOURCES = [
    # GitHub releases / changelogs that are publicly accessible
    ("Anthropic SDK Python", "https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/CHANGELOG.md"),
    ("OpenAI SDK Python",    "https://raw.githubusercontent.com/openai/openai-python/main/CHANGELOG.md"),
]

def fetch_announcements():
    """
    Fetch recent changelog entries from SDK repos.
    Falls back to curated summaries if not accessible.
    """
    print("Fetching announcements...")
    items = []

    for label, url in ANNOUNCEMENT_SOURCES:
        text = fetch_text(url)
        if not text:
            continue

        # extract first 2 changelog entries (## [x.x.x] blocks)
        blocks = re.split(r"\n##\s+", text)
        for block in blocks[1:4]:  # skip header, take up to 3 entries
            lines = block.strip().split("\n")
            if not lines:
                continue
            version_line = lines[0].strip()
            # get first 5 meaningful bullet lines
            bullets = [l.strip("- ").strip()
                       for l in lines[1:]
                       if l.strip().startswith("-") and len(l.strip()) > 5][:5]
            if bullets:
                items.append({
                    "source":   label,
                    "version":  version_line,
                    "bullets":  bullets,
                    "impact":   classify_impact(bullets),
                })

    if not items:
        items = get_announcement_fallback()

    print(f"  Found {len(items)} announcement entries")
    return items

def classify_impact(bullets):
    """Simple keyword classification for what this affects."""
    text = " ".join(bullets).lower()
    impacts = []
    if any(w in text for w in ["model", "claude", "gpt", "opus", "sonnet", "haiku"]):
        impacts.append("Model updates")
    if any(w in text for w in ["price", "cost", "token", "billing", "rate"]):
        impacts.append("Pricing")
    if any(w in text for w in ["context", "window", "token limit", "memory"]):
        impacts.append("Context / memory")
    if any(w in text for w in ["tool", "function", "agent", "agentic"]):
        impacts.append("Agentic / tools")
    if any(w in text for w in ["api", "endpoint", "sdk", "client"]):
        impacts.append("API / SDK")
    if any(w in text for w in ["deprecat", "retire", "remov", "sunset"]):
        impacts.append("Deprecations")
    if any(w in text for w in ["security", "safety", "guardrail", "filter"]):
        impacts.append("Safety / security")
    return impacts if impacts else ["General update"]

def get_announcement_fallback():
    return [
        {
            "source":  "Anthropic",
            "version": "Recent highlights (June 2026)",
            "bullets": [
                "Claude Opus 4.8 released with 1M context window and enhanced agentic coding capabilities",
                "Prompt caching now generally available for Sonnet 4.6 and Opus 4.6",
                "Batch API output limit raised to 300k tokens for Opus and Sonnet 4.6",
                "Claude Sonnet 4.6 and Opus 4.6 now support 1M token context on Amazon Bedrock and Vertex AI",
            ],
            "impact": ["Model updates", "Context / memory", "API / SDK"],
        },
        {
            "source":  "OpenAI",
            "version": "Recent highlights (June 2026)",
            "bullets": [
                "o4-mini released as a cost-effective reasoning model",
                "GPT-4o now supports structured outputs natively",
                "Realtime API available for voice and audio applications",
            ],
            "impact": ["Model updates", "API / SDK"],
        },
    ]


# ── Compose final JSON ────────────────────────────────────────────────────────

def build_data():
    anthropic = fetch_anthropic_models()
    openai    = fetch_openai_models()
    others    = get_other_models()
    announcements = fetch_announcements()

    return {
        "updated_at": NOW,
        "models": anthropic + openai + others,
        "announcements": announcements,
        "pricing_note": (
            "Prices are per 1M input tokens (USD). Output tokens typically cost 3–5× more. "
            "Pricing not available via API for most providers — verify at each provider's docs. "
            f"Last updated: {NOW}."
        ),
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"AI Cheatsheet Updater — {NOW}")
    print("-" * 50)

    data = build_data()

    print("-" * 50)
    print(f"Total models: {len(data['models'])}")
    print(f"Announcements: {len(data['announcements'])}")

    if DRY_RUN:
        print("\n[DRY RUN] Output preview:")
        print(json.dumps(data, indent=2)[:2000])
    else:
        output_path = os.path.join(os.path.dirname(__file__), OUTPUT)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved to {output_path}")
