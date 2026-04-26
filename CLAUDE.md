# Eviction Command — Document Generator Service
## CLAUDE.md — Living Project Context

> Update this file whenever architecture decisions change, new open items surface, or important context is discovered.

---

## What This Is

A hosted Python microservice (Railway) that replaces Make.com for Eviction Command's fulfillment step. When a client submits an intake form in GHL, this service:

1. Receives the GHL webhook
2. Selects the correct Claude Sonnet prompt (state × notice type = 15 combinations)
3. Calls Claude Sonnet to generate the eviction document
4. Converts the document to a styled PDF via WeasyPrint
5. Uploads the PDF to a Google Drive client folder
6. Notifies GHL: moves opportunity to "Pending Review" + adds a note with the Drive link

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| Framework | FastAPI | Single endpoint: `POST /generate` |
| PDF Generation | WeasyPrint | Self-hosted, free. Switch to PDFShift if quality is unacceptable. |
| AI Router | OpenRouter via OpenAI SDK | `base_url=https://openrouter.ai/api/v1` — model set by `OPENROUTER_MODEL` env var |
| Storage | Google Drive API v3 | Service account auth (not OAuth) |
| Hosting | Railway | Nixpacks builder + system deps for WeasyPrint |
| Config | python-dotenv | |

---

## Project Structure

```
reportgenerator/
├── CLAUDE.md                        ← this file
├── main.py                          ← FastAPI app, POST /generate endpoint
├── requirements.txt
├── railway.toml
├── nixpacks.toml                    ← WeasyPrint system deps (Pango, Cairo, etc.)
├── .env.example
├── .env                             ← local only, never commit
├── prompts/
│   ├── georgia_3day.txt             ← COMPLETE reference prompt
│   └── [14 more — fill in later]   ← Legal requirements need Sunshine review first
├── services/
│   ├── llm_service.py               ← OpenRouter call (model = OPENROUTER_MODEL env var)
│   ├── pdf_service.py               ← WeasyPrint HTML→PDF
│   └── drive_service.py             ← Google Drive upload, folder creation
├── models/
│   └── intake_form.py               ← Pydantic model for GHL webhook payload
├── utils/
│   └── prompt_loader.py             ← State+notice_type → prompt file, variable injection
├── tests/
│   ├── test_prompt_loader.py
│   ├── test_claude_service.py
│   ├── test_pdf_service.py
│   ├── test_drive_service.py
│   └── test_main.py
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-04-27-eviction-doc-generator.md
```

---

## Environment Variables

```bash
# OpenRouter — swap OPENROUTER_MODEL value to change LLM instantly, no code changes
OPENROUTER_API_KEY=
# Model examples: anthropic/claude-sonnet-4-5, openai/gpt-4o, google/gemini-pro-1.5
OPENROUTER_MODEL=anthropic/claude-sonnet-4-5

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_JSON=   # Base64-encoded service account JSON
GOOGLE_DRIVE_PARENT_FOLDER_ID=   # Root folder in Drive for all client docs

# GHL
GHL_WEBHOOK_SECRET=              # Validates incoming GHL webhooks
GHL_API_KEY=                     # For updating stage + adding notes
GHL_LOCATION_ID=                 # Eviction Command sub-account location ID
GHL_PENDING_REVIEW_STAGE_ID=     # Actual stage ID — get from GHL sub-account

# Service
PORT=8000
ENVIRONMENT=production
```

---

## Key Decisions & Rationale

### Prompt files are `.txt`, not in a database
Simple, version-controlled, easy to edit. 15 files total. Legal copy needs Sunshine review before finalizing — file-per-state makes it easy to iterate.

### OpenRouter over direct Anthropic SDK
OpenRouter lets us swap models by changing one env var (`OPENROUTER_MODEL`) with zero code changes. Uses the OpenAI SDK with `base_url=https://openrouter.ai/api/v1`. Default model: `anthropic/claude-sonnet-4-5`.

### WeasyPrint over PDFShift
WeasyPrint is free and self-hosted. PDFShift is a paid external API. Start with WeasyPrint; switch if PDF rendering quality is unacceptable after testing.

### Service account auth for Google Drive
No OAuth flows or user login needed. Service account JSON stored as Base64 env var so Railway can hold it without file uploads.

### GHL: if GHL update fails, still return 200
Document is already generated and in Drive. GHL note failure is non-critical — log it, don't fail the whole request.

### Claude API: if it fails, return 500 immediately
Do not upload a partial or empty document. Fail fast.

---

## Prompt File Naming Convention

```
{state_key}_{notice_key}.txt

State keys:   georgia, texas, south_carolina, tennessee, indiana
Notice keys:  3day, 3060day, ud

Examples:
  georgia_3day.txt
  texas_ud.txt
  south_carolina_3060day.txt
```

**Notice type → key mapping:**
- `3-Day Pay or Quit` → `3day`
- `30-Day Notice` → `3060day`
- `60-Day Notice` → `3060day`
- `Full UD Package` → `ud`

---

## GHL API Notes

> The requirements doc references GHL API v1 endpoints — verify actual v2 paths before implementing.

- Move opportunity stage: `PUT /opportunities/{opportunity_id}` with `{ "stageId": "..." }`
- Add contact note: `POST /contacts/{contact_id}/notes` with `{ "body": "..." }`
- Auth header: `Authorization: Bearer {GHL_API_KEY}`

**Stage IDs are not guessable — must be pulled from the Eviction Command sub-account.**

---

## Prompt File Status

| File | Status |
|---|---|
| `georgia_3day.txt` | COMPLETE — O.C.G.A. § 44-7-50(c), 2024 HB 404, statutory serving method, attorney review notes |
| `georgia_3060day.txt` | COMPLETE — O.C.G.A. § 44-7-7, 60-day notice, research sources, attorney review notes |
| `georgia_ud.txt` | COMPLETE — O.C.G.A. § 44-7-49 to 59, 4-document Dispossessory Package, attorney review notes |
| `texas_*.txt` (3 files) | NOT STARTED — needs legal research + Sunshine review |
| `south_carolina_*.txt` (3 files) | NOT STARTED — needs legal research + Sunshine review |
| `tennessee_*.txt` (3 files) | NOT STARTED — needs legal research + Sunshine review |
| `indiana_*.txt` (3 files) | NOT STARTED — needs legal research + Sunshine review |

> Note: Georgia prompts were researched using Justia, county court websites, and Georgia Legal Aid (retrieved April 2026). Each file includes `⚠️ NEEDS ATTORNEY REVIEW` notes for Sunshine.

---

## Open Items (Do Not Build Until Resolved)

| Item | Status | Who |
|---|---|---|
| Remaining 12 prompt files | Blocked — legal research + Sunshine review needed | Sunshine |
| GHL stage ID for "Pending Review" | Need from GHL sub-account | Zee |
| Google Drive parent folder ID | Create folder in Drive, copy ID | Zee |
| PDFShift vs WeasyPrint final call | Test PDF quality first | After first deploy |
| GHL API v2 endpoint verification | Verify before implementing GHL calls | Dev |

---

## Local Dev Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill env vars
cp .env.example .env

# Run locally
uvicorn main:app --reload --port 8000

# Run tests
pytest tests/ -v
```

---

## Testing Checklist (Before Going Live)

- [ ] POST /generate with Georgia 3-Day dummy payload → correct prompt loads, variables populate, Claude returns doc, PDF renders, Drive upload succeeds, GHL stage moves, GHL note appears
- [ ] Repeat for all 15 state/notice combinations
- [ ] Missing optional fields → "N/A" not blank/error
- [ ] Invalid state/notice type → 400 (not 500)
- [ ] Claude API failure → 500, GHL stage NOT moved
- [ ] Drive upload failure → 500, GHL stage NOT moved
- [ ] Deploy to Railway + one full end-to-end test with real GHL form

---

## Deployment (Railway)

```bash
# railway.toml handles build + start command
# nixpacks.toml handles WeasyPrint system deps

# After deploy, set env vars in Railway dashboard
# PORT is set automatically by Railway
```

---

*Last updated: 2026-04-27*
