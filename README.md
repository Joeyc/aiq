# AI Cheatsheet — Auto-Updating

A self-hosted, auto-updating AI concepts cheatsheet. The HTML reads
from `ai_data.json` on load. A Python script regenerates the JSON
weekly via GitHub Actions.

## Files

| File | Purpose |
|------|---------|
| `AI_Concepts_Cheatsheet.html` | The cheatsheet — reads `ai_data.json` on load |
| `update_data.py` | Updater script — queries APIs and writes `ai_data.json` |
| `ai_data.json` | Generated data file — committed by GitHub Actions weekly |
| `.github/workflows/update.yml` | GitHub Actions schedule |

## Setup

### 1. Fork or clone this repo on GitHub

### 2. Add API keys as GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret name | Where to get it |
|-------------|----------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `OPENAI_API_KEY` | platform.openai.com/api-keys |

Both are optional — the script falls back to curated data if keys
are absent. But with real keys, Anthropic and OpenAI model lists
are pulled live from their APIs.

### 3. Enable GitHub Pages

Go to **Settings → Pages** and set:
- Source: `Deploy from a branch`
- Branch: `main` / `root`

Your cheatsheet will be live at:
`https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/AI_Concepts_Cheatsheet.html`

### 4. (Optional) Run manually

```bash
# Install dependencies
pip install requests beautifulsoup4 feedparser

# Run with your API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
python update_data.py

# Dry run (no file write)
python update_data.py --dry-run
```

## How it updates

```
Every Monday 09:00 SGT
        │
        ▼
GitHub Actions runs update_data.py
        │
        ├── Anthropic /v1/models API  ──► live model list
        ├── OpenAI /v1/models API     ──► live model list
        ├── SDK changelogs (GitHub)   ──► recent announcements
        └── Curated fallbacks         ──► Google, Meta, Mistral, xAI
        │
        ▼
Writes ai_data.json
        │
        ▼
Commits & pushes to repo
        │
        ▼
GitHub Pages serves updated cheatsheet
```

## What gets updated automatically

- Anthropic model IDs (new models appear when released to API)
- OpenAI model IDs (new models appear when released to API)
- Recent changelog entries from Anthropic and OpenAI SDKs
- `updated_at` timestamp shown in the cheatsheet

## What requires manual updates

- Pricing (not available via API — scraped sites block bots)
- Google, Meta, Mistral, xAI models (no open API)
- Context window sizes for non-Anthropic/OpenAI models
- New cheatsheet sections (AI vs chatbot, local vs cloud, etc.)

To update manually, edit the relevant section in `update_data.py`
and either push to GitHub (Actions will pick it up) or run locally.

## Updating pricing manually

Open `update_data.py` and edit the `ANTHROPIC_TIER_MAP`,
`get_anthropic_fallback()`, `get_openai_fallback()`, or
`get_other_models()` functions. Prices are in `input_price` fields.

Check current pricing at:
- Anthropic: https://docs.anthropic.com/en/docs/about-claude/pricing
- OpenAI:    https://openai.com/api/pricing
- Google:    https://ai.google.dev/pricing
- Mistral:   https://mistral.ai/technology/#pricing
