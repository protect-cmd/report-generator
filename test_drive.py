import os
import base64
import json
from dotenv import dotenv_values
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

_env = dotenv_values(".env")
print("Keys found in .env:", list(_env.keys()))
for k, v in _env.items():
    print(f"  {k}: len={len(v or '')}, first_40={repr((v or '')[:40])}")

try:
    # Step 1 — decode credentials
    creds_b64 = _env.get("GOOGLE_DRIVE_CREDENTIALS_JSON")
    print(f"\nCREDS length: {len(creds_b64) if creds_b64 else 'MISSING/EMPTY'}")
    creds_json = base64.b64decode(creds_b64).decode("utf-8")
    creds_dict = json.loads(creds_json)
    print("✓ Credentials decoded OK")
    print(f"  Service account: {creds_dict.get('client_email')}")

    # Step 2 — build Drive client
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)
    print("✓ Drive client built OK")

    # Step 3 — try listing files in the folder
    folder_id = _env.get("GOOGLE_DRIVE_PARENT_FOLDER_ID")
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name)"
    ).execute()
    print(f"✓ Folder access OK — {len(results.get('files', []))} files found")

except Exception as e:
    print(f"✗ FAILED: {e}")
