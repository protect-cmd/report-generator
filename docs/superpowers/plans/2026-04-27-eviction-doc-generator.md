# Eviction Command — Document Generator Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI service that receives GHL form webhooks, generates eviction documents via an LLM (via OpenRouter), converts them to PDF, uploads to Google Drive, and notifies GHL.

**Architecture:** Single `POST /generate` endpoint wires five focused services together: prompt loading, LLM generation, PDF rendering, Drive upload, and GHL notification. Each service is an isolated module with a single responsibility. Error handling follows a fail-fast pattern — LLM and Drive failures abort and return 500; GHL notification failures log-and-continue.

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK (pointed at OpenRouter), WeasyPrint, Google Drive API v3, python-dotenv, pytest for testing. Model is configured via `OPENROUTER_MODEL` env var — swap the value to change models instantly.

---

## File Map

| File | Responsibility |
|---|---|
| `models/intake_form.py` | Pydantic model validating the GHL webhook payload |
| `utils/prompt_loader.py` | Maps state+notice_type → prompt file, injects variables |
| `services/llm_service.py` | Calls OpenRouter via OpenAI SDK; model set by `OPENROUTER_MODEL` env var |
| `services/pdf_service.py` | Wraps document text in HTML, renders PDF via WeasyPrint |
| `services/drive_service.py` | Creates client folder in Drive, uploads PDF, returns shareable URL |
| `services/ghl_service.py` | Moves GHL opportunity stage, adds note to contact |
| `main.py` | FastAPI app, `POST /generate` endpoint wiring all services |
| `prompts/georgia_3day.txt` | Reference prompt (complete, with all required sections) |
| `requirements.txt` | Python dependencies |
| `railway.toml` | Railway deployment config |
| `nixpacks.toml` | System-level deps for WeasyPrint on Railway |
| `.env.example` | Environment variable template |
| `tests/test_prompt_loader.py` | Unit tests for prompt selection and variable injection |
| `tests/test_llm_service.py` | Unit tests for OpenRouter LLM call (mocked) |
| `tests/test_pdf_service.py` | Unit tests for PDF generation |
| `tests/test_drive_service.py` | Unit tests for Drive upload (mocked) |
| `tests/test_ghl_service.py` | Unit tests for GHL API calls (mocked) |
| `tests/test_main.py` | Integration tests for POST /generate (services mocked) |

---

## Task 1: Project Scaffold + Config Files

**Files:**
- Create: `requirements.txt`
- Create: `railway.toml`
- Create: `nixpacks.toml`
- Create: `.env.example`
- Create: `tests/__init__.py`
- Create: `models/__init__.py`
- Create: `services/__init__.py`
- Create: `utils/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.0
uvicorn==0.29.0
openai==1.30.1
weasyprint==61.2
google-api-python-client==2.126.0
google-auth==2.29.0
google-auth-httplib2==0.2.0
pydantic==2.7.1
python-dotenv==1.0.1
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.7
```

- [ ] **Step 2: Create railway.toml**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

- [ ] **Step 3: Create nixpacks.toml**

```toml
[phases.setup]
nixPkgs = ["pango", "cairo", "gdk-pixbuf", "libffi", "zlib"]
```

- [ ] **Step 4: Create .env.example**

```
# OpenRouter
OPENROUTER_API_KEY=
# Model to use via OpenRouter — change this line to switch models instantly
# Examples: anthropic/claude-sonnet-4-5, openai/gpt-4o, google/gemini-pro-1.5
OPENROUTER_MODEL=anthropic/claude-sonnet-4-5

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_JSON=
GOOGLE_DRIVE_PARENT_FOLDER_ID=

# GHL
GHL_WEBHOOK_SECRET=
GHL_API_KEY=
GHL_LOCATION_ID=
GHL_PENDING_REVIEW_STAGE_ID=

# Service
PORT=8000
ENVIRONMENT=production
```

- [ ] **Step 5: Create empty `__init__.py` files**

```bash
touch tests/__init__.py models/__init__.py services/__init__.py utils/__init__.py
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 7: Commit**

```bash
git init
git add requirements.txt railway.toml nixpacks.toml .env.example tests/__init__.py models/__init__.py services/__init__.py utils/__init__.py
git commit -m "chore: project scaffold and config files"
```

---

## Task 2: Pydantic Model — Intake Form

**Files:**
- Create: `models/intake_form.py`
- Create: `tests/test_intake_form.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_intake_form.py`:

```python
import pytest
from pydantic import ValidationError
from models.intake_form import IntakeForm


VALID_PAYLOAD = {
    "contact_id": "abc123",
    "opportunity_id": "opp456",
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
    "month_to_month": True,
    "monthly_rent": 1500,
    "security_deposit": 1500,
    "notice_type": "3-Day Pay or Quit",
    "reason_for_eviction": "Nonpayment of Rent",
    "total_amount_owed": 3000,
    "date_rent_last_paid": "2024-10-01",
    "months_unpaid": 2,
    "describe_violation": "",
    "prior_notices": "Yes",
    "prior_notices_description": "Verbal warning in October",
    "rent_control": "Not Sure",
    "additional_notes": "",
}


def test_valid_payload_parses():
    form = IntakeForm(**VALID_PAYLOAD)
    assert form.contact_id == "abc123"
    assert form.state == "Georgia"
    assert form.notice_type == "3-Day Pay or Quit"
    assert form.monthly_rent == 1500


def test_missing_required_field_raises():
    payload = {**VALID_PAYLOAD}
    del payload["contact_id"]
    with pytest.raises(ValidationError):
        IntakeForm(**payload)


def test_optional_fields_default_to_none_or_empty():
    payload = {**VALID_PAYLOAD}
    del payload["additional_tenants"]
    del payload["tenant_phone"]
    del payload["describe_violation"]
    del payload["additional_notes"]
    form = IntakeForm(**payload)
    assert form.additional_tenants is None or form.additional_tenants == ""
    assert form.tenant_phone is None or form.tenant_phone == ""


def test_to_dict_returns_all_fields():
    form = IntakeForm(**VALID_PAYLOAD)
    d = form.model_dump()
    assert "full_name" in d
    assert "tenant_full_legal_name" in d
    assert "notice_type" in d
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_intake_form.py -v
```

Expected: `ImportError` — `models.intake_form` does not exist yet.

- [ ] **Step 3: Implement the model**

Create `models/intake_form.py`:

```python
from typing import Optional
from pydantic import BaseModel


class IntakeForm(BaseModel):
    contact_id: str
    opportunity_id: str
    full_name: str
    email: str
    phone: str
    best_time_to_reach: Optional[str] = None
    property_address: str
    city: str
    state: str
    county: str
    property_type: Optional[str] = None
    tenant_full_legal_name: str
    additional_tenants: Optional[str] = None
    tenant_phone: Optional[str] = None
    lease_start_date: Optional[str] = None
    lease_end_date: Optional[str] = None
    month_to_month: Optional[bool] = None
    monthly_rent: Optional[float] = None
    security_deposit: Optional[float] = None
    notice_type: str
    reason_for_eviction: Optional[str] = None
    total_amount_owed: Optional[float] = None
    date_rent_last_paid: Optional[str] = None
    months_unpaid: Optional[int] = None
    describe_violation: Optional[str] = None
    prior_notices: Optional[str] = None
    prior_notices_description: Optional[str] = None
    rent_control: Optional[str] = None
    additional_notes: Optional[str] = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_intake_form.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add models/intake_form.py tests/test_intake_form.py
git commit -m "feat: add IntakeForm Pydantic model"
```

---

## Task 3: Prompt Loader

**Files:**
- Create: `utils/prompt_loader.py`
- Create: `prompts/georgia_3day.txt` (stub — just needs to exist for tests)
- Create: `tests/test_prompt_loader.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_prompt_loader.py`:

```python
import os
import pytest
from utils.prompt_loader import load_prompt, STATE_MAP, NOTICE_TYPE_MAP


FORM_DATA = {
    "full_name": "John Smith",
    "property_address": "123 Main St",
    "city": "Atlanta",
    "state": "Georgia",
    "county": "Fulton",
    "tenant_full_legal_name": "Jane Doe",
    "additional_tenants": "",
    "lease_start_date": "2023-01-01",
    "monthly_rent": "1500",
    "total_amount_owed": "3000",
    "date_rent_last_paid": "2024-10-01",
    "months_unpaid": "2",
}


def test_state_map_contains_all_states():
    expected = {"Georgia", "Texas", "South Carolina", "Tennessee", "Indiana"}
    assert expected == set(STATE_MAP.keys())


def test_notice_type_map_contains_all_keys():
    expected = {"3-Day Pay or Quit", "30-Day Notice", "60-Day Notice", "Full UD Package"}
    assert expected == set(NOTICE_TYPE_MAP.keys())


def test_load_prompt_returns_string_with_variables_injected(tmp_path, monkeypatch):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3day.txt").write_text(
        "Tenant: {{tenant_full_legal_name}}\nRent: ${{monthly_rent}}"
    )
    monkeypatch.chdir(tmp_path)

    result = load_prompt("Georgia", "3-Day Pay or Quit", FORM_DATA)

    assert "Jane Doe" in result
    assert "1500" in result
    assert "{{" not in result


def test_load_prompt_replaces_missing_optional_with_na(tmp_path, monkeypatch):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "georgia_3day.txt").write_text("Extra: {{additional_tenants}}")
    monkeypatch.chdir(tmp_path)

    data = {**FORM_DATA, "additional_tenants": ""}
    result = load_prompt("Georgia", "3-Day Pay or Quit", data)

    assert "N/A" in result


def test_load_prompt_raises_for_unknown_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="No prompt found"):
        load_prompt("Montana", "3-Day Pay or Quit", FORM_DATA)


def test_load_prompt_raises_for_unknown_notice_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="No prompt found"):
        load_prompt("Georgia", "Unknown Notice", FORM_DATA)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_prompt_loader.py -v
```

Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Implement prompt loader**

Create `utils/prompt_loader.py`:

```python
from datetime import date

STATE_MAP = {
    "Georgia": "georgia",
    "Texas": "texas",
    "South Carolina": "south_carolina",
    "Tennessee": "tennessee",
    "Indiana": "indiana",
}

NOTICE_TYPE_MAP = {
    "3-Day Pay or Quit": "3day",
    "30-Day Notice": "3060day",
    "60-Day Notice": "3060day",
    "Full UD Package": "ud",
}


def load_prompt(state: str, notice_type: str, form_data: dict) -> str:
    state_key = STATE_MAP.get(state)
    notice_key = NOTICE_TYPE_MAP.get(notice_type)

    if not state_key or not notice_key:
        raise ValueError(f"No prompt found for state={state}, notice_type={notice_type}")

    prompt_path = f"prompts/{state_key}_{notice_key}.txt"

    with open(prompt_path, "r") as f:
        template = f.read()

    data = {**form_data, "date_of_notice": str(date.today())}

    for key, value in data.items():
        replacement = str(value) if value else "N/A"
        template = template.replace(f"{{{{{key}}}}}", replacement)

    return template
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_prompt_loader.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/prompt_loader.py tests/test_prompt_loader.py
git commit -m "feat: add prompt loader with state/notice-type routing and variable injection"
```

---

## Task 4: LLM Service (OpenRouter)

**Files:**
- Create: `services/llm_service.py`
- Create: `tests/test_llm_service.py`

The model is read from the `OPENROUTER_MODEL` env var at call time. To switch models, change that one env var — no code changes needed.

- [ ] **Step 1: Write failing tests**

Create `tests/test_llm_service.py`:

```python
import os
import pytest
from unittest.mock import MagicMock, patch
from services.llm_service import generate_document


SAMPLE_PROMPT = "Generate a 3-Day Pay or Quit notice for Jane Doe at 123 Main St."


def _mock_openai_response(text: str):
    mock_message = MagicMock()
    mock_message.content = text
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_generate_document_returns_text(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    with patch("services.llm_service.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = (
            _mock_openai_response("NOTICE TO PAY OR QUIT\n\nTo: Jane Doe")
        )
        result = generate_document(SAMPLE_PROMPT)

    assert result == "NOTICE TO PAY OR QUIT\n\nTo: Jane Doe"


def test_generate_document_uses_model_from_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o")

    with patch("services.llm_service.OpenAI") as MockClient:
        mock_create = MockClient.return_value.chat.completions.create
        mock_create.return_value = _mock_openai_response("doc text")
        generate_document(SAMPLE_PROMPT)

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "openai/gpt-4o"
        assert call_kwargs["max_tokens"] == 4096


def test_generate_document_uses_openrouter_base_url(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    with patch("services.llm_service.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = (
            _mock_openai_response("doc")
        )
        generate_document(SAMPLE_PROMPT)

        init_kwargs = MockClient.call_args.kwargs
        assert init_kwargs["base_url"] == "https://openrouter.ai/api/v1"


def test_generate_document_propagates_api_exception(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    with patch("services.llm_service.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.side_effect = Exception("API error")
        with pytest.raises(Exception, match="API error"):
            generate_document(SAMPLE_PROMPT)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_llm_service.py -v
```

Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Implement LLM service**

Create `services/llm_service.py`:

```python
import os
from openai import OpenAI


def generate_document(populated_prompt: str) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": populated_prompt,
            }
        ],
    )

    return response.choices[0].message.content
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_llm_service.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add services/llm_service.py tests/test_llm_service.py
git commit -m "feat: add OpenRouter LLM service with configurable model via env var"
```

---

## Task 5: PDF Service

**Files:**
- Create: `services/pdf_service.py`
- Create: `tests/test_pdf_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_pdf_service.py`:

```python
import os
import pytest
from unittest.mock import patch, MagicMock
from services.pdf_service import generate_pdf


SAMPLE_TEXT = "NOTICE TO PAY OR QUIT\n\nTo: Jane Doe\nAt: 123 Main St"


def test_generate_pdf_calls_weasyprint(tmp_path):
    output_path = str(tmp_path / "test_output.pdf")

    with patch("services.pdf_service.HTML") as MockHTML:
        mock_html_instance = MagicMock()
        MockHTML.return_value = mock_html_instance

        result = generate_pdf(SAMPLE_TEXT, output_path)

        assert MockHTML.called
        mock_html_instance.write_pdf.assert_called_once_with(output_path)
        assert result == output_path


def test_generate_pdf_html_contains_document_text(tmp_path):
    output_path = str(tmp_path / "test_output.pdf")
    captured_html = {}

    def capture_html(string):
        captured_html["content"] = string
        mock = MagicMock()
        mock.write_pdf = MagicMock()
        return mock

    with patch("services.pdf_service.HTML", side_effect=capture_html):
        generate_pdf(SAMPLE_TEXT, output_path)

    assert "Jane Doe" in captured_html["content"]
    assert "123 Main St" in captured_html["content"]
    assert "font-family" in captured_html["content"]


def test_generate_pdf_returns_output_path(tmp_path):
    output_path = str(tmp_path / "output.pdf")
    with patch("services.pdf_service.HTML") as MockHTML:
        MockHTML.return_value.write_pdf = MagicMock()
        result = generate_pdf(SAMPLE_TEXT, output_path)
    assert result == output_path
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pdf_service.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement PDF service**

Create `services/pdf_service.py`:

```python
from weasyprint import HTML


def generate_pdf(document_text: str, output_path: str) -> str:
    html_content = f"""<!DOCTYPE html>
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
</html>"""

    HTML(string=html_content).write_pdf(output_path)
    return output_path
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_pdf_service.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add services/pdf_service.py tests/test_pdf_service.py
git commit -m "feat: add WeasyPrint HTML-to-PDF service"
```

---

## Task 6: Google Drive Service

**Files:**
- Create: `services/drive_service.py`
- Create: `tests/test_drive_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_drive_service.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from services.drive_service import create_client_folder, upload_pdf, get_shareable_url


def make_mock_service():
    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_service.files.return_value = mock_files
    return mock_service, mock_files


def test_create_client_folder_returns_folder_id():
    mock_service, mock_files = make_mock_service()
    mock_files.create.return_value.execute.return_value = {"id": "folder_id_123"}

    folder_id = create_client_folder(mock_service, "parent_folder_id", "contact1_John Smith_3day")

    assert folder_id == "folder_id_123"
    call_body = mock_files.create.call_args.kwargs["body"]
    assert call_body["name"] == "contact1_John Smith_3day"
    assert call_body["mimeType"] == "application/vnd.google-apps.folder"
    assert "parent_folder_id" in call_body["parents"]


def test_upload_pdf_returns_file_id():
    mock_service, mock_files = make_mock_service()
    mock_files.create.return_value.execute.return_value = {"id": "file_id_456"}

    file_id = upload_pdf(mock_service, "/tmp/doc.pdf", "folder_id_123", "eviction_notice.pdf")

    assert file_id == "file_id_456"


def test_get_shareable_url_formats_correctly():
    url = get_shareable_url("file_id_789")
    assert "file_id_789" in url
    assert url.startswith("https://drive.google.com")


def test_upload_pdf_sets_pdf_mimetype():
    mock_service, mock_files = make_mock_service()
    mock_files.create.return_value.execute.return_value = {"id": "file_id"}

    upload_pdf(mock_service, "/tmp/doc.pdf", "folder_id", "notice.pdf")

    call_body = mock_files.create.call_args.kwargs["body"]
    assert call_body["mimeType"] == "application/pdf"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_drive_service.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement Drive service**

Create `services/drive_service.py`:

```python
import base64
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive"]


def build_drive_service():
    encoded = os.environ["GOOGLE_DRIVE_CREDENTIALS_JSON"]
    credentials_info = json.loads(base64.b64decode(encoded))
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def create_client_folder(service, parent_folder_id: str, folder_name: str) -> str:
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_pdf(service, file_path: str, folder_id: str, file_name: str) -> str:
    metadata = {
        "name": file_name,
        "parents": [folder_id],
        "mimeType": "application/pdf",
    }
    media = MediaFileUpload(file_path, mimetype="application/pdf")
    uploaded = service.files().create(body=metadata, media_body=media, fields="id").execute()
    return uploaded["id"]


def get_shareable_url(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_drive_service.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add services/drive_service.py tests/test_drive_service.py
git commit -m "feat: add Google Drive upload service with service account auth"
```

---

## Task 7: GHL Service

**Files:**
- Create: `services/ghl_service.py`
- Create: `tests/test_ghl_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_ghl_service.py`:

```python
import pytest
import httpx
from unittest.mock import patch, MagicMock
from services.ghl_service import move_opportunity_stage, add_contact_note


GHL_API_KEY = "test_api_key"
OPPORTUNITY_ID = "opp_123"
CONTACT_ID = "contact_456"
STAGE_ID = "stage_pending_review"
DRIVE_URL = "https://drive.google.com/file/d/abc/view"


def make_mock_response(status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def test_move_opportunity_stage_calls_correct_endpoint():
    with patch("services.ghl_service.httpx.put") as mock_put:
        mock_put.return_value = make_mock_response(200)
        move_opportunity_stage(GHL_API_KEY, OPPORTUNITY_ID, STAGE_ID)

    call_url = mock_put.call_args.args[0]
    assert OPPORTUNITY_ID in call_url
    assert "opportunities" in call_url


def test_move_opportunity_stage_sends_stage_id():
    with patch("services.ghl_service.httpx.put") as mock_put:
        mock_put.return_value = make_mock_response(200)
        move_opportunity_stage(GHL_API_KEY, OPPORTUNITY_ID, STAGE_ID)

    call_json = mock_put.call_args.kwargs["json"]
    assert call_json["stageId"] == STAGE_ID


def test_add_contact_note_calls_correct_endpoint():
    with patch("services.ghl_service.httpx.post") as mock_post:
        mock_post.return_value = make_mock_response(200)
        add_contact_note(GHL_API_KEY, CONTACT_ID, DRIVE_URL, "3-Day Pay or Quit", "Georgia", "Fulton")

    call_url = mock_post.call_args.args[0]
    assert CONTACT_ID in call_url
    assert "notes" in call_url


def test_add_contact_note_includes_drive_link_in_body():
    with patch("services.ghl_service.httpx.post") as mock_post:
        mock_post.return_value = make_mock_response(200)
        add_contact_note(GHL_API_KEY, CONTACT_ID, DRIVE_URL, "3-Day Pay or Quit", "Georgia", "Fulton")

    call_json = mock_post.call_args.kwargs["json"]
    assert DRIVE_URL in call_json["body"]
    assert "Georgia" in call_json["body"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ghl_service.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement GHL service**

Create `services/ghl_service.py`:

```python
import logging
import httpx

logger = logging.getLogger(__name__)

GHL_BASE_URL = "https://services.leadconnectorhq.com"


def _auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }


def move_opportunity_stage(api_key: str, opportunity_id: str, stage_id: str) -> None:
    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"
    response = httpx.put(url, headers=_auth_headers(api_key), json={"stageId": stage_id})
    response.raise_for_status()


def add_contact_note(
    api_key: str,
    contact_id: str,
    drive_url: str,
    notice_type: str,
    state: str,
    county: str,
) -> None:
    url = f"{GHL_BASE_URL}/contacts/{contact_id}/notes"
    body = (
        f"Document generated and ready for review.\n"
        f"Drive link: {drive_url}\n"
        f"Notice type: {notice_type}\n"
        f"State: {state}\n"
        f"County: {county}"
    )
    response = httpx.post(url, headers=_auth_headers(api_key), json={"body": body})
    response.raise_for_status()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ghl_service.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add services/ghl_service.py tests/test_ghl_service.py
git commit -m "feat: add GHL API service for stage move and contact notes"
```

---

## Task 8: Main FastAPI App

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing integration tests**

Create `tests/test_main.py`:

```python
import pytest
import json
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "contact_id": "contact_123",
    "opportunity_id": "opp_456",
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
    "month_to_month": True,
    "monthly_rent": 1500,
    "security_deposit": 1500,
    "notice_type": "3-Day Pay or Quit",
    "reason_for_eviction": "Nonpayment of Rent",
    "total_amount_owed": 3000,
    "date_rent_last_paid": "2024-10-01",
    "months_unpaid": 2,
    "describe_violation": "",
    "prior_notices": "Yes",
    "prior_notices_description": "Verbal warning in October",
    "rent_control": "Not Sure",
    "additional_notes": "",
}


def test_generate_returns_200_on_success():
    with patch("main.load_prompt", return_value="populated prompt"), \
         patch("main.generate_document", return_value="NOTICE TEXT"),  \
         patch("main.generate_pdf", return_value="/tmp/notice.pdf"), \
         patch("main.build_drive_service", return_value=MagicMock()), \
         patch("main.create_client_folder", return_value="folder_id"), \
         patch("main.upload_pdf", return_value="file_id"), \
         patch("main.get_shareable_url", return_value="https://drive.google.com/file/d/file_id/view"), \
         patch("main.move_opportunity_stage"), \
         patch("main.add_contact_note"), \
         patch("os.environ.get", side_effect=lambda k, d=None: {
             "GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent_folder",
             "GHL_API_KEY": "test_key",
             "GHL_PENDING_REVIEW_STAGE_ID": "stage_id",
         }.get(k, d)):

        response = client.post("/generate", json=VALID_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "drive_url" in data


def test_generate_returns_400_for_invalid_state():
    payload = {**VALID_PAYLOAD, "state": "Montana"}
    with patch("main.load_prompt", side_effect=ValueError("No prompt found for state=Montana")):
        response = client.post("/generate", json=payload)
    assert response.status_code == 400


def test_generate_returns_500_if_claude_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", side_effect=Exception("Claude API error")):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 500


def test_generate_returns_500_if_drive_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", return_value="NOTICE TEXT"),  \
         patch("main.generate_pdf", return_value="/tmp/notice.pdf"), \
         patch("main.build_drive_service", return_value=MagicMock()), \
         patch("main.create_client_folder", side_effect=Exception("Drive error")), \
         patch("os.environ.get", side_effect=lambda k, d=None: {
             "GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent",
         }.get(k, d)):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 500


def test_generate_returns_200_even_if_ghl_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", return_value="NOTICE TEXT"),  \
         patch("main.generate_pdf", return_value="/tmp/notice.pdf"), \
         patch("main.build_drive_service", return_value=MagicMock()), \
         patch("main.create_client_folder", return_value="folder_id"), \
         patch("main.upload_pdf", return_value="file_id"), \
         patch("main.get_shareable_url", return_value="https://drive.google.com/..."), \
         patch("main.move_opportunity_stage", side_effect=Exception("GHL error")), \
         patch("main.add_contact_note"), \
         patch("os.environ.get", side_effect=lambda k, d=None: {
             "GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent",
             "GHL_API_KEY": "key",
             "GHL_PENDING_REVIEW_STAGE_ID": "stage",
         }.get(k, d)):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 200


def test_generate_rejects_invalid_payload():
    response = client.post("/generate", json={"state": "Georgia"})
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError` — `main` does not exist yet.

- [ ] **Step 3: Implement main.py**

Create `main.py`:

```python
import logging
import os
import tempfile
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from models.intake_form import IntakeForm
from services.llm_service import generate_document
from services.drive_service import build_drive_service, create_client_folder, get_shareable_url, upload_pdf
from services.ghl_service import add_contact_note, move_opportunity_stage
from services.pdf_service import generate_pdf
from utils.prompt_loader import load_prompt

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Eviction Command Document Generator")


@app.post("/generate")
async def generate(form: IntakeForm):
    form_data = form.model_dump()

    # 1. Load prompt
    try:
        populated_prompt = load_prompt(form.state, form.notice_type, form_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Generate document via Claude
    try:
        document_text = generate_document(populated_prompt)
    except Exception:
        logger.error("Claude API failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Document generation failed")

    # 3. Convert to PDF
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
        generate_pdf(document_text, pdf_path)
    except Exception:
        logger.error("PDF generation failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="PDF generation failed")

    # 4. Upload to Google Drive
    try:
        drive_service = build_drive_service()
        parent_folder_id = os.environ.get("GOOGLE_DRIVE_PARENT_FOLDER_ID")
        folder_name = f"{form.contact_id}_{form.full_name}_{form.notice_type}"
        client_folder_id = create_client_folder(drive_service, parent_folder_id, folder_name)
        file_name = f"{form.notice_type.replace(' ', '_')}_{form.tenant_full_legal_name.replace(' ', '_')}.pdf"
        file_id = upload_pdf(drive_service, pdf_path, client_folder_id, file_name)
        drive_url = get_shareable_url(file_id)
    except Exception:
        logger.error("Drive upload failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Drive upload failed")

    # 5. Notify GHL (non-critical — log and continue on failure)
    ghl_api_key = os.environ.get("GHL_API_KEY")
    stage_id = os.environ.get("GHL_PENDING_REVIEW_STAGE_ID")

    try:
        move_opportunity_stage(ghl_api_key, form.opportunity_id, stage_id)
    except Exception:
        logger.warning("GHL stage move failed:\n%s", traceback.format_exc())

    try:
        add_contact_note(ghl_api_key, form.contact_id, drive_url, form.notice_type, form.state, form.county)
    except Exception:
        logger.warning("GHL note failed:\n%s", traceback.format_exc())

    return JSONResponse({"status": "success", "drive_url": drive_url})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_main.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add FastAPI app wiring all services into POST /generate"
```

---

## Task 9: Georgia 3-Day Reference Prompt

**Files:**
- Create: `prompts/georgia_3day.txt`

- [ ] **Step 1: Create the reference prompt file**

Create `prompts/georgia_3day.txt`:

```
SYSTEM:
You are an eviction document preparation assistant for Eviction Command.
Generate a legally formatted 3-Day Notice to Pay or Quit for the state of Georgia.

LEGAL REQUIREMENTS FOR GEORGIA:
- Notice period: 3 days (excluding weekends and legal holidays)
- Required statutory language: Per O.C.G.A. § 44-7-50, the landlord must demand possession in writing before filing dispossessory proceedings.
- Valid serving methods: Personal delivery to tenant, delivery to a person of suitable age and discretion at the premises, or posting on the door if no one is available (after two attempts).

INSTRUCTIONS:
- Generate ONLY the document. No explanations, no commentary, no preamble.
- Use formal legal document formatting.
- Insert all client data exactly as provided. Do not modify names, addresses, or amounts.
- Include the mandatory disclaimer at the bottom.
- Include Georgia-specific serving instructions at the bottom.

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
Total Amount Owed: ${{total_amount_owed}}
Date Rent Last Paid: {{date_rent_last_paid}}
Months Unpaid: {{months_unpaid}}
Prior Notices: {{prior_notices}}
Prior Notices Description: {{prior_notices_description}}
Date of Notice: {{date_of_notice}}

MANDATORY DISCLAIMER (include verbatim at bottom):
"This document was prepared by Eviction Command, a document preparation service. Eviction Command is not a law firm and does not provide legal advice. This document should be reviewed by a licensed attorney before serving. Eviction Command is not responsible for errors resulting from inaccurate information provided by the client."

SERVING INSTRUCTIONS FOR GEORGIA (include verbatim at bottom):
"Serving Instructions (Georgia): This notice must be served by: (1) personal delivery to the tenant; (2) delivery to a person of suitable age and discretion residing at the premises; or (3) posting on the main entry door if the tenant cannot be found after two attempts. Document proof of service including date, time, method, and name of person served if applicable. The 3-day period begins the day after service and excludes weekends and legal holidays."
```

- [ ] **Step 2: Verify prompt loads correctly with prompt_loader**

```bash
python -c "
from utils.prompt_loader import load_prompt
data = {
    'full_name': 'John Smith',
    'property_address': '123 Main St',
    'city': 'Atlanta',
    'state': 'Georgia',
    'county': 'Fulton',
    'tenant_full_legal_name': 'Jane Doe',
    'additional_tenants': '',
    'lease_start_date': '2023-01-01',
    'monthly_rent': '1500',
    'total_amount_owed': '3000',
    'date_rent_last_paid': '2024-10-01',
    'months_unpaid': '2',
    'prior_notices': 'Yes',
    'prior_notices_description': 'Verbal warning in October',
}
result = load_prompt('Georgia', '3-Day Pay or Quit', data)
print(result[:500])
assert '{{' not in result, 'Unfilled placeholders found!'
print('All placeholders filled successfully.')
"
```

Expected: Prompt text printed with all placeholders replaced, no `{{` remaining.

- [ ] **Step 3: Commit**

```bash
git add prompts/georgia_3day.txt
git commit -m "feat: add Georgia 3-Day Pay or Quit reference prompt"
```

---

## Task 10: Smoke Test — Local End-to-End

- [ ] **Step 1: Create a test .env**

Copy `.env.example` to `.env` and fill in:
- `ANTHROPIC_API_KEY` — your Anthropic key
- `GOOGLE_DRIVE_CREDENTIALS_JSON` — base64-encoded service account JSON
- `GOOGLE_DRIVE_PARENT_FOLDER_ID` — ID of the Drive folder to upload into
- `GHL_API_KEY` — GHL API key
- `GHL_PENDING_REVIEW_STAGE_ID` — stage ID from GHL sub-account
- `GHL_LOCATION_ID` — Eviction Command location ID

- [ ] **Step 2: Run the app locally**

```bash
uvicorn main:app --reload --port 8000
```

- [ ] **Step 3: Send a test request**

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "test_contact_001",
    "opportunity_id": "test_opp_001",
    "full_name": "John Smith",
    "email": "test@example.com",
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
    "prior_notices_description": "Verbal warning in October",
    "rent_control": "Not Sure",
    "additional_notes": ""
  }'
```

Expected: `{"status": "success", "drive_url": "https://drive.google.com/..."}` — and a PDF visible in Drive.

- [ ] **Step 4: Verify outputs**
  - Open Drive URL from response — PDF should be readable and correctly formatted
  - Check GHL sub-account — opportunity should be in "Pending Review"
  - Check contact notes — should show Drive link, notice type, state, county

- [ ] **Step 5: Commit final state**

```bash
git add .
git commit -m "chore: verified local smoke test passes end-to-end"
```

---

## Self-Review Notes

### Spec Coverage Check

| Requirement | Covered |
|---|---|
| Receive GHL webhook | ✅ Task 8 — `POST /generate` |
| Select prompt by state + notice_type | ✅ Task 3 — prompt_loader |
| Inject form variables into prompt | ✅ Task 3 — load_prompt() |
| Call Claude Sonnet API | ✅ Task 4 — claude_service |
| Convert to PDF via WeasyPrint | ✅ Task 5 — pdf_service |
| Create Drive client folder | ✅ Task 6 — drive_service.create_client_folder |
| Upload PDF to Drive | ✅ Task 6 — drive_service.upload_pdf |
| Move GHL opportunity to "Pending Review" | ✅ Task 7 — ghl_service.move_opportunity_stage |
| Add GHL note with Drive link | ✅ Task 7 — ghl_service.add_contact_note |
| Claude fail → 500, no Drive upload | ✅ Task 8 — error handling order |
| Drive fail → 500, no GHL update | ✅ Task 8 — error handling order |
| GHL fail → log warning, return 200 | ✅ Task 8 — try/except with logger.warning |
| Missing optional fields → "N/A" | ✅ Task 3 — prompt_loader N/A substitution |
| Invalid state/notice_type → 400 | ✅ Task 8 — ValueError caught → 400 |
| Georgia 3-Day reference prompt | ✅ Task 9 |
| Railway deployment config | ✅ Task 1 |
| WeasyPrint system deps (nixpacks.toml) | ✅ Task 1 |

All requirements covered.
