# AIQ — AI Quick Reference

Your AI quick reference for interviews, teaching, and staying current.
Covers tokens, models, generative AI, agentic AI, RAG, fine-tuning,
local vs cloud LLMs, privacy, artifacts, and more.

The HTML reads from `ai_data.json` on load. A Python script
regenerates the JSON weekly via GitHub Actions — so the models
table and announcements section stay current automatically.

## Files

| File | Purpose |
|------|---------|
| `aiq.html` | AIQ — the reference site |
| `update_data.py` | Updater script — queries APIs, writes `ai_data.json` |
| `ai_data.json` | Auto-generated data file, committed weekly |
| `.github/workflows/update.yml` | GitHub Actions schedule (every Monday 09:00 SGT) |
| `README.md` | This file |

## Setup (15 minutes)

### 1. Create a GitHub repo and push all files

Put `update.yml` at `.github/workflows/update.yml`.
Everything else goes in the root.

### 2. Add API keys as GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Where to get it |
|--------|----------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `OPENAI_API_KEY` | platform.openai.com/api-keys |

Both are optional — the script uses curated fallback data if keys
are absent. With real keys, Anthropic and OpenAI model lists are
pulled live from their APIs each week.

### 3. Enable GitHub Pages

Go to **Settings → Pages** and set:
- Source: `Deploy from a branch`
- Branch: `main` / root folder

AIQ will be live at:
```
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/aiq.html
```

### 4. Trigger the first data update

Go to **Actions → Update AIQ data → Run workflow**.
This generates a fresh `ai_data.json` and commits it.
After that, it runs automatically every Monday.

### 5. (Optional) Run the updater locally

```bash
# Install dependencies
pip install requests beautifulsoup4 feedparser

# Set your API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# Run
python update_data.py

# Preview without saving
python update_data.py --dry-run
```

## How the auto-update works

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
GitHub Pages serves updated AIQ
```

## What updates automatically

- Anthropic model IDs (new models appear when released to the API)
- OpenAI model IDs (new models appear when released to the API)
- Recent changelog entries from Anthropic and OpenAI SDK repos
- `updated_at` timestamp shown in the Models tab

## What needs manual updates

- **Pricing** — not available via API; provider sites block scrapers
- **Google, Meta, Mistral, xAI models** — no open API for these
- **Context window sizes** for non-Anthropic/OpenAI models
- **New content sections** in the HTML (AI vs chatbot, local vs cloud, etc.)

To update manually: edit `update_data.py`, push to GitHub,
and Actions will pick it up on the next run (or trigger manually).

## Updating pricing

Open `update_data.py` and edit the `input_price` fields in:
- `get_anthropic_fallback()` — Anthropic models
- `get_openai_fallback()` — OpenAI models
- `get_other_models()` — Google, Meta, Mistral, xAI

Current pricing sources:
- Anthropic: https://docs.anthropic.com/en/docs/about-claude/pricing
- OpenAI:    https://openai.com/api/pricing
- Google:    https://ai.google.dev/pricing
- Mistral:   https://mistral.ai/technology/#pricing

## Content tabs

| Tab | Contents |
|-----|----------|
| Tokens | What tokens are, cost formula, worked examples |
| Models | Live model table (auto-updated) + announcements |
| AI types | Traditional vs generative vs agentic AI |
| RAG & fine-tuning | Three adaptation methods, RAG step-by-step |
| Agent structure | Brain, tools, memory, loop, safeguards |
| Artifacts | Claude artifacts, unique features per AI product, Perplexity vs ChatGPT vs Claude |
| AI landscape | Who makes what, commonly confused names, open vs closed |
| Local vs cloud | Full comparison, hardware requirements, Ollama setup |
| Privacy & training | How to give models knowledge, data leak prevention, PDPA |
| AI vs chatbot | Rule-based vs LLM-powered, when to use each |
| Using agents well | 8 principles, common mistakes, prompt patterns |
| Glossary | 28 terms, useful links |
