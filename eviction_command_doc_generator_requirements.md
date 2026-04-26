# Eviction Command — Document Generator Service
## Requirements for Claude Code

---

## Overview

Build a hosted Python service deployed on Railway that:
1. Receives a webhook from GHL when an intake form is submitted
2. Selects the correct Claude Sonnet prompt based on state + notice type
3. Calls the Claude Sonnet API to generate the eviction document
4. Converts the generated text to a formatted PDF
5. Uploads the PDF to a specific Google Drive folder
6. Notifies GHL to move the pipeline stage and trigger Sunshine's review notification

This service replaces Make.com for the fulfillment step entirely.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| PDF Generation | WeasyPrint |
| AI | Anthropic Claude Sonnet API (`claude-sonnet-4-20250514`) |
| Storage | Google Drive API v3 |
| Hosting | Railway |
| Environment config | python-dotenv |

---

## Project Structure

```
eviction-doc-generator/
├── main.py                  # FastAPI app entry point
├── requirements.txt         # Python dependencies
├── railway.toml             # Railway deployment config
├── .env.example             # Environment variable template
├── prompts/
│   ├── georgia_3day.txt
│   ├── georgia_3060day.txt
│   ├── georgia_ud.txt
│   ├── texas_3day.txt
│   ├── texas_3060day.txt
│   ├── texas_ud.txt
│   ├── south_carolina_3day.txt
│   ├── south_carolina_3060day.txt
│   ├── south_carolina_ud.txt
│   ├── tennessee_3day.txt
│   ├── tennessee_3060day.txt
│   ├── tennessee_ud.txt
│   ├── indiana_3day.txt
│   ├── indiana_3060day.txt
│   └── indiana_ud.txt
├── services/
│   ├── claude_service.py    # Claude API call logic
│   ├── pdf_service.py       # WeasyPrint PDF generation
│   └── drive_service.py     # Google Drive upload logic
├── models/
│   └── intake_form.py       # Pydantic model for form payload
└── utils/
    └── prompt_loader.py     # Loads correct prompt file based on state + notice type
```

---

## Environment Variables

Create a `.env` file using `.env.example` as the template:

```
# Anthropic
ANTHROPIC_API_KEY=

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_JSON=   # Base64-encoded service account JSON
GOOGLE_DRIVE_PARENT_FOLDER_ID=   # Root folder ID for all client documents

# GHL
GHL_WEBHOOK_SECRET=              # For validating incoming GHL webhooks
GHL_API_KEY=                     # For updating pipeline stage + triggering notifications
GHL_LOCATION_ID=                 # Eviction Command sub-account location ID

# Service
PORT=8000
ENVIRONMENT=production
```

---

## Webhook Endpoint

### `POST /generate`

Receives the GHL form submission payload.

**Expected payload (from GHL form webhook):**

```json
{
  "contact_id": "ghl_contact_id",
  "opportunity_id": "ghl_opportunity_id",
  "full_name": "John Smith",
  "email": "john@example.com",
  "phone": "5551234567",
  "best_time_to_reach": "Morning",
  "property_address": "123 Main St Unit 4",
  "city": "Atlanta",
  "state": "Georgia",
  "county": "Fulton",
  "property_type": "Single Family Home",
  "tenant_full_legal_name": "Jane Doe",
  "additional_tenants": "",
  "tenant_phone": "",
  "lease_start_date": "2023-01-01",
  "lease_end_date": "",
  "month_to_month": true,
  "monthly_rent": 1500,
  "security_deposit": 1500,
  "notice_type": "3-Day Pay or Quit",
  "reason_for_eviction": "Nonpayment of Rent",
  "total_amount_owed": 3000,
  "date_rent_last_paid": "2024-10-01",
  "months_unpaid": 2,
  "describe_violation": "",
  "prior_notices": "Yes",
  "prior_notices_description": "Verbal warning given in October",
  "rent_control": "Not Sure",
  "additional_notes": ""
}
```

**What the endpoint does:**

```
1. Validate payload with Pydantic model
2. Determine prompt file key from state + notice_type
3. Load correct prompt file from /prompts/
4. Inject all form fields into prompt as variables
5. Call Claude Sonnet API with system prompt + populated user message
6. Receive generated document text
7. Convert text to styled PDF via WeasyPrint
8. Create client folder in Google Drive: "{contact_id}_{full_name}_{notice_type}"
9. Upload PDF to that folder
10. Call GHL API to:
    a. Move opportunity to stage "Pending Review"
    b. Add internal note to contact with Google Drive PDF link
11. Return 200 with { "status": "success", "drive_url": "..." }
```

**Error handling:**
- If Claude API fails → return 500, do NOT upload partial document
- If Drive upload fails → return 500, log error, do NOT update GHL stage
- If GHL update fails → log warning but return 200 (document is already generated and uploaded)
- All errors must be logged with full traceback

---

## Prompt File Format

Each `.txt` file in `/prompts/` follows this structure.
The service loads the file and replaces `{{variable}}` placeholders with form data before sending to Claude.

```
SYSTEM:
You are an eviction document preparation assistant for Eviction Command.
Generate a legally formatted [NOTICE TYPE] for the state of [STATE].

LEGAL REQUIREMENTS FOR [STATE]:
- Notice period: [X days — hardcoded per state]
- Required statutory language: [exact language — hardcoded per state]
- Valid serving methods: [list — hardcoded per state]

INSTRUCTIONS:
- Generate ONLY the document. No explanations, no commentary, no preamble.
- Use formal legal document formatting.
- Insert all client data exactly as provided. Do not modify names, addresses, or amounts.
- Include the mandatory disclaimer at the bottom.
- Include state-specific serving instructions at the bottom.

CLIENT DATA:
Landlord Name: {{full_name}}
Landlord Address: {{property_address}}, {{city}}, {{state}}
Tenant Name: {{tenant_full_legal_name}}
Additional Tenants: {{additional_tenants}}
Property Address: {{property_address}}
City: {{city}}
County: {{county}}
State: {{state}}
Lease Start Date: {{lease_start_date}}
Monthly Rent: ${{monthly_rent}}
[NOTICE-TYPE SPECIFIC FIELDS INJECTED HERE]
Date of Notice: {{date_of_notice}}

MANDATORY DISCLAIMER (include verbatim at bottom):
"This document was prepared by Eviction Command, a document preparation 
service. Eviction Command is not a law firm and does not provide legal 
advice. This document should be reviewed by a licensed attorney before 
serving. Eviction Command is not responsible for errors resulting from 
inaccurate information provided by the client."

SERVING INSTRUCTIONS FOR {{state}} (include verbatim at bottom):
[Hardcoded per state in each prompt file]
```

**Prompt file naming convention:**
```
{state_lowercase_underscored}_{notice_type_key}.txt

Keys:
  3-Day Pay or Quit         → 3day
  30/60-Day Notice to Vacate → 3060day
  Full Unlawful Detainer Package → ud

Examples:
  georgia_3day.txt
  texas_ud.txt
  south_carolina_3060day.txt
```

---

## Prompt Loader Logic

```python
# utils/prompt_loader.py

NOTICE_TYPE_MAP = {
    "3-Day Pay or Quit": "3day",
    "30-Day Notice": "3060day",
    "60-Day Notice": "3060day",
    "Full UD Package": "ud"
}

STATE_MAP = {
    "Georgia": "georgia",
    "Texas": "texas",
    "South Carolina": "south_carolina",
    "Tennessee": "tennessee",
    "Indiana": "indiana"
}

def load_prompt(state: str, notice_type: str, form_data: dict) -> str:
    state_key = STATE_MAP.get(state)
    notice_key = NOTICE_TYPE_MAP.get(notice_type)

    if not state_key or not notice_key:
        raise ValueError(f"No prompt found for state={state}, notice_type={notice_type}")

    prompt_path = f"prompts/{state_key}_{notice_key}.txt"

    with open(prompt_path, "r") as f:
        template = f.read()

    # Replace all {{variable}} placeholders
    for key, value in form_data.items():
        template = template.replace(f"{{{{{key}}}}}", str(value) if value else "N/A")

    return template
```

---

## Claude API Call

```python
# services/claude_service.py

import anthropic

def generate_document(populated_prompt: str) -> str:
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": populated_prompt
            }
        ]
    )

    return message.content[0].text
```

---

## PDF Generation

```python
# services/pdf_service.py
# Uses WeasyPrint to convert HTML → PDF
# Document text from Claude is wrapped in styled HTML before conversion

def generate_pdf(document_text: str, output_path: str) -> str:
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            font-family: 'Times New Roman', Times, serif;
            font-size: 12pt;
            line-height: 1.6;
            margin: 1in;
            color: #000;
        }}
        h1 {{ font-size: 14pt; text-align: center; text-transform: uppercase; }}
        .disclaimer {{
            font-size: 10pt;
            border-top: 1px solid #000;
            margin-top: 40px;
            padding-top: 10px;
            color: #333;
        }}
        .serving-instructions {{
            font-size: 10pt;
            margin-top: 20px;
            padding: 10px;
            border: 1px solid #ccc;
        }}
    </style>
    </head>
    <body>
        {document_text.replace(chr(10), '<br>')}
    </body>
    </html>
    """

    from weasyprint import HTML
    HTML(string=html_content).write_pdf(output_path)
    return output_path
```

---

## Google Drive Upload

```python
# services/drive_service.py

# Use service account credentials (not OAuth)
# Credentials stored as Base64-encoded JSON in env var GOOGLE_DRIVE_CREDENTIALS_JSON
# Create client folder named: {contact_id}_{full_name}_{notice_type}
# Upload PDF to that folder
# Return shareable Drive URL of the uploaded file
```

---

## GHL API Calls

After successful PDF upload, make two GHL API calls:

**1. Move opportunity stage to "Pending Review"**
```
PUT https://rest.gohighlevel.com/v1/opportunities/{opportunity_id}
Headers: Authorization: Bearer {GHL_API_KEY}
Body: { "stageId": "{pending_review_stage_id}" }
```

**2. Add internal note to contact with Drive link**
```
POST https://rest.gohighlevel.com/v1/contacts/{contact_id}/notes
Headers: Authorization: Bearer {GHL_API_KEY}
Body: {
  "body": "Document generated and ready for review.\nDrive link: {drive_url}\nNotice type: {notice_type}\nState: {state}\nCounty: {county}"
}
```

> Note: Look up the correct GHL API v2 endpoint structure — v1 above is for reference only. Verify actual endpoint paths from GHL API docs before implementing.

---

## Requirements.txt

```
fastapi==0.111.0
uvicorn==0.29.0
anthropic==0.25.0
weasyprint==61.2
google-api-python-client==2.126.0
google-auth==2.29.0
google-auth-httplib2==0.2.0
pydantic==2.7.1
python-dotenv==1.0.1
httpx==0.27.0
```

---

## Railway Config

```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

---

## railway.toml Nixpacks Note

WeasyPrint requires system-level dependencies (Pango, Cairo, GDK-PixBuf).
Add a `nixpacks.toml` to install them:

```toml
# nixpacks.toml
[phases.setup]
nixPkgs = ["pango", "cairo", "gdk-pixbuf", "libffi", "zlib"]
```

---

## Testing Checklist (Before Going Live)

```
□ POST /generate with Georgia 3-Day Pay or Quit dummy payload
  → Confirm correct prompt file loads
  → Confirm all variables populate correctly
  → Confirm Claude returns a properly formatted document
  → Confirm PDF renders correctly (open the file)
  → Confirm PDF uploads to correct Google Drive folder
  → Confirm GHL opportunity moves to "Pending Review"
  → Confirm GHL note appears on contact with Drive link

□ Repeat above for all 15 state/notice type combinations with dummy data

□ Test missing optional fields (additional_tenants, tenant_phone, etc.)
  → Confirm "N/A" appears, not blank or error

□ Test invalid state/notice type combination
  → Confirm 400 error returned, not 500

□ Test Claude API timeout
  → Confirm 500 returned and GHL stage NOT moved

□ Test Drive upload failure
  → Confirm 500 returned and GHL stage NOT moved

□ Deploy to Railway and run one full end-to-end test with real GHL form submission
```

---

## What Claude Code Should Build First

1. Project scaffold — folder structure, all empty files
2. `models/intake_form.py` — Pydantic model with all form fields
3. `utils/prompt_loader.py` — prompt selection and variable injection
4. `services/claude_service.py` — Claude API call
5. `services/pdf_service.py` — WeasyPrint HTML → PDF
6. `services/drive_service.py` — Google Drive upload with service account
7. `main.py` — FastAPI app with `/generate` endpoint wiring all services together
8. `prompts/georgia_3day.txt` — build one complete prompt as reference
9. `requirements.txt` and `railway.toml` and `nixpacks.toml`
10. `.env.example`

**Do NOT build all 15 prompt files** — build one complete reference prompt (Georgia 3-Day) and provide a template that Zee fills in per state. The legal requirements per state need to be researched and verified before the prompts are written.

---

## Open Items (Do Not Build Until Resolved)

| Item | Reason |
|---|---|
| All 15 prompt files | Legal requirements per state need research + Sunshine review before hardcoding |
| GHL stage IDs | Need actual stage IDs from the Eviction Command sub-account (not guessable) |
| Google Drive parent folder ID | Needs to be created in Drive and ID copied |
| PDFShift vs WeasyPrint final decision | WeasyPrint is free and self-hosted; if PDF quality is not acceptable, switch to PDFShift (paid, external API) |
