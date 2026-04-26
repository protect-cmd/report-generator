import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive"]


def build_drive_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


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
