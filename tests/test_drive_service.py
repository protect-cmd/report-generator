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


def test_create_client_folder_sends_correct_metadata():
    mock_service, mock_files = make_mock_service()
    mock_files.create.return_value.execute.return_value = {"id": "folder_id"}

    create_client_folder(mock_service, "parent_folder_id", "contact1_John Smith_3day")

    call_body = mock_files.create.call_args.kwargs["body"]
    assert call_body["name"] == "contact1_John Smith_3day"
    assert call_body["mimeType"] == "application/vnd.google-apps.folder"
    assert "parent_folder_id" in call_body["parents"]


def test_upload_pdf_returns_file_id():
    mock_service, mock_files = make_mock_service()
    mock_files.create.return_value.execute.return_value = {"id": "file_id_456"}

    with patch("services.drive_service.MediaFileUpload"):
        file_id = upload_pdf(mock_service, "/tmp/doc.pdf", "folder_id_123", "eviction_notice.pdf")

    assert file_id == "file_id_456"


def test_upload_pdf_sets_pdf_mimetype():
    mock_service, mock_files = make_mock_service()
    mock_files.create.return_value.execute.return_value = {"id": "file_id"}

    with patch("services.drive_service.MediaFileUpload"):
        upload_pdf(mock_service, "/tmp/doc.pdf", "folder_id", "notice.pdf")

    call_body = mock_files.create.call_args.kwargs["body"]
    assert call_body["mimeType"] == "application/pdf"


def test_upload_pdf_sets_correct_parent_folder():
    mock_service, mock_files = make_mock_service()
    mock_files.create.return_value.execute.return_value = {"id": "file_id"}

    with patch("services.drive_service.MediaFileUpload"):
        upload_pdf(mock_service, "/tmp/doc.pdf", "folder_id_789", "notice.pdf")

    call_body = mock_files.create.call_args.kwargs["body"]
    assert "folder_id_789" in call_body["parents"]


def test_get_shareable_url_formats_correctly():
    url = get_shareable_url("file_id_789")
    assert "file_id_789" in url
    assert url.startswith("https://drive.google.com")


def test_get_shareable_url_is_view_link():
    url = get_shareable_url("abc123")
    assert "/file/d/abc123/" in url


def test_build_drive_service_reads_env_and_decodes_credentials(monkeypatch):
    import base64
    import json
    from services.drive_service import build_drive_service

    fake_creds = {
        "type": "service_account",
        "project_id": "test",
        "private_key_id": "key1",
        "private_key": "fake-key",
        "client_email": "test@test.iam.gserviceaccount.com",
        "client_id": "123",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    encoded = base64.b64encode(json.dumps(fake_creds).encode()).decode()
    monkeypatch.setenv("GOOGLE_DRIVE_CREDENTIALS_JSON", encoded)

    with patch("services.drive_service.service_account.Credentials.from_service_account_info") as mock_creds, \
         patch("services.drive_service.build") as mock_build:
        mock_creds.return_value = MagicMock()
        mock_build.return_value = MagicMock()

        build_drive_service()

        mock_creds.assert_called_once()
        call_args = mock_creds.call_args.args[0]
        assert call_args["type"] == "service_account"
        mock_build.assert_called_once_with("drive", "v3", credentials=mock_creds.return_value)
