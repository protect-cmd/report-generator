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
