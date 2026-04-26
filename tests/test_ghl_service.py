import pytest
import httpx
from unittest.mock import patch, MagicMock
from services.ghl_service import move_opportunity_stage, add_contact_note, GHL_TIMEOUT_SECONDS


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


def test_move_opportunity_stage_sends_auth_header():
    with patch("services.ghl_service.httpx.put") as mock_put:
        mock_put.return_value = make_mock_response(200)
        move_opportunity_stage(GHL_API_KEY, OPPORTUNITY_ID, STAGE_ID)

    call_headers = mock_put.call_args.kwargs["headers"]
    assert call_headers["Authorization"] == f"Bearer {GHL_API_KEY}"


def test_move_opportunity_stage_calls_raise_for_status():
    mock_resp = make_mock_response(200)
    with patch("services.ghl_service.httpx.put", return_value=mock_resp):
        move_opportunity_stage(GHL_API_KEY, OPPORTUNITY_ID, STAGE_ID)

    mock_resp.raise_for_status.assert_called_once()


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


def test_add_contact_note_includes_state_county_and_notice_type():
    with patch("services.ghl_service.httpx.post") as mock_post:
        mock_post.return_value = make_mock_response(200)
        add_contact_note(GHL_API_KEY, CONTACT_ID, DRIVE_URL, "3-Day Pay or Quit", "Georgia", "Fulton")

    call_json = mock_post.call_args.kwargs["json"]
    assert "Georgia" in call_json["body"]
    assert "Fulton" in call_json["body"]
    assert "3-Day Pay or Quit" in call_json["body"]


def test_http_calls_use_explicit_timeout():
    with patch("services.ghl_service.httpx.put") as mock_put, \
         patch("services.ghl_service.httpx.post") as mock_post:
        mock_put.return_value = make_mock_response(200)
        mock_post.return_value = make_mock_response(200)

        move_opportunity_stage(GHL_API_KEY, OPPORTUNITY_ID, STAGE_ID)
        add_contact_note(GHL_API_KEY, CONTACT_ID, DRIVE_URL, "3-Day Pay or Quit", "Georgia", "Fulton")

    assert mock_put.call_args.kwargs["timeout"] == GHL_TIMEOUT_SECONDS
    assert mock_post.call_args.kwargs["timeout"] == GHL_TIMEOUT_SECONDS


def test_add_contact_note_calls_raise_for_status():
    mock_resp = make_mock_response(200)
    with patch("services.ghl_service.httpx.post", return_value=mock_resp):
        add_contact_note(GHL_API_KEY, CONTACT_ID, DRIVE_URL, "3-Day Pay or Quit", "Georgia", "Fulton")

    mock_resp.raise_for_status.assert_called_once()
