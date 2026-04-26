import pytest
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

DRIVE_URL = "https://drive.google.com/file/d/file_id/view?usp=sharing"


def _full_success_patches():
    return [
        patch("main.load_prompt", return_value="populated prompt"),
        patch("main.generate_document", return_value="NOTICE TEXT"),
        patch("main.generate_pdf", return_value="/tmp/notice.pdf"),
        patch("main.build_drive_service", return_value=MagicMock()),
        patch("main.create_client_folder", return_value="folder_id"),
        patch("main.upload_pdf", return_value="file_id"),
        patch("main.get_shareable_url", return_value=DRIVE_URL),
        patch("main.move_opportunity_stage"),
        patch("main.add_contact_note"),
        patch.dict("os.environ", {
            "GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent_folder",
            "GHL_API_KEY": "test_key",
            "GHL_PENDING_REVIEW_STAGE_ID": "stage_id",
        }),
    ]


def test_generate_returns_200_on_success():
    with _full_success_patches()[0], _full_success_patches()[1], \
         _full_success_patches()[2], _full_success_patches()[3], \
         _full_success_patches()[4], _full_success_patches()[5], \
         _full_success_patches()[6], _full_success_patches()[7], \
         _full_success_patches()[8], _full_success_patches()[9]:
        response = client.post("/generate", json=VALID_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["drive_url"] == DRIVE_URL


def test_generate_returns_400_for_invalid_state():
    with patch("main.load_prompt", side_effect=ValueError("No prompt found for state=Montana")):
        response = client.post("/generate", json={**VALID_PAYLOAD, "state": "Montana"})
    assert response.status_code == 400


def test_generate_returns_500_if_llm_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", side_effect=Exception("LLM error")):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 500


def test_generate_returns_500_if_pdf_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", return_value="TEXT"), \
         patch("main.generate_pdf", side_effect=Exception("PDF error")):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 500


def test_generate_returns_500_if_drive_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", return_value="TEXT"), \
         patch("main.generate_pdf", return_value="/tmp/notice.pdf"), \
         patch("main.build_drive_service", return_value=MagicMock()), \
         patch("main.create_client_folder", side_effect=Exception("Drive error")), \
         patch.dict("os.environ", {"GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent"}):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 500


def test_generate_returns_200_even_if_ghl_stage_move_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", return_value="TEXT"), \
         patch("main.generate_pdf", return_value="/tmp/notice.pdf"), \
         patch("main.build_drive_service", return_value=MagicMock()), \
         patch("main.create_client_folder", return_value="folder_id"), \
         patch("main.upload_pdf", return_value="file_id"), \
         patch("main.get_shareable_url", return_value=DRIVE_URL), \
         patch("main.move_opportunity_stage", side_effect=Exception("GHL error")), \
         patch("main.add_contact_note"), \
         patch.dict("os.environ", {
             "GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent",
             "GHL_API_KEY": "key",
             "GHL_PENDING_REVIEW_STAGE_ID": "stage",
         }):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["drive_url"] == DRIVE_URL


def test_generate_returns_200_even_if_ghl_note_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", return_value="TEXT"), \
         patch("main.generate_pdf", return_value="/tmp/notice.pdf"), \
         patch("main.build_drive_service", return_value=MagicMock()), \
         patch("main.create_client_folder", return_value="folder_id"), \
         patch("main.upload_pdf", return_value="file_id"), \
         patch("main.get_shareable_url", return_value=DRIVE_URL), \
         patch("main.move_opportunity_stage"), \
         patch("main.add_contact_note", side_effect=Exception("Note error")), \
         patch.dict("os.environ", {
             "GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent",
             "GHL_API_KEY": "key",
             "GHL_PENDING_REVIEW_STAGE_ID": "stage",
         }):
        response = client.post("/generate", json=VALID_PAYLOAD)
    assert response.status_code == 200


def test_generate_rejects_invalid_pydantic_payload():
    response = client.post("/generate", json={"state": "Georgia"})
    assert response.status_code == 422


def test_generate_ghl_not_called_if_drive_fails():
    with patch("main.load_prompt", return_value="prompt"), \
         patch("main.generate_document", return_value="TEXT"), \
         patch("main.generate_pdf", return_value="/tmp/notice.pdf"), \
         patch("main.build_drive_service", return_value=MagicMock()), \
         patch("main.create_client_folder", side_effect=Exception("Drive error")), \
         patch("main.move_opportunity_stage") as mock_stage, \
         patch("main.add_contact_note") as mock_note, \
         patch.dict("os.environ", {"GOOGLE_DRIVE_PARENT_FOLDER_ID": "parent"}):
        response = client.post("/generate", json=VALID_PAYLOAD)

    assert response.status_code == 500
    mock_stage.assert_not_called()
    mock_note.assert_not_called()
