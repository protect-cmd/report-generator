"""
Run once locally to get a Google OAuth refresh token for Drive uploads.

Prerequisites:
  1. Create an OAuth 2.0 "Desktop app" credential in Google Cloud Console
     (same project as the service account)
  2. Download the JSON and save it as credentials.json in the project root
  3. pip install google-auth-oauthlib

Usage:
  python scripts/get_oauth_token.py

Copy the printed refresh token into your .env as GOOGLE_OAUTH_REFRESH_TOKEN.
The client_id and client_secret come from the same credentials.json.
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials.json"

if not CREDENTIALS_FILE.exists():
    raise FileNotFoundError(
        f"credentials.json not found at {CREDENTIALS_FILE}\n"
        "Download it from Google Cloud Console → APIs & Services → Credentials"
    )

flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
creds = flow.run_local_server(port=0)

raw = json.loads(CREDENTIALS_FILE.read_text())
client = raw.get("installed") or raw.get("web", {})

print("\n=== Add these to your .env ===")
print(f"GOOGLE_CLIENT_ID={client['client_id']}")
print(f"GOOGLE_CLIENT_SECRET={client['client_secret']}")
print(f"GOOGLE_OAUTH_REFRESH_TOKEN={creds.refresh_token}")
