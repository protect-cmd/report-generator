"""One-off test script — send both emails to zeannkirstendc@gmail.com."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

# Route both internal recipients to Zee for this test
os.environ["SUNSHINE_EMAIL"] = "zeannkirstendc@gmail.com"
os.environ["ADMIN_EMAIL"] = "zeannkirstendc@gmail.com"

from services.email_service import send_sunshine_notification, send_client_delivery

# --- 1. Internal review email ---
ok1 = send_sunshine_notification(
    drive_url="https://drive.google.com/file/d/test123/view",
    notice_type="3-Day Pay or Quit",
    state="georgia",
    tenant_name="John Smith",
    contact_id="contact_abc123",
)
print("Sunshine notification:", "SENT" if ok1 else "FAILED")

# --- 2. Client delivery email (tiny dummy PDF so the attachment shows up) ---
dummy_pdf = b"%PDF-1.4 dummy"

ok2 = send_client_delivery(
    client_email="zeannkirstendc@gmail.com",
    client_name="Jane Landlord",
    notice_type="3-Day Pay or Quit",
    state="georgia",
    county="Fulton",
    property_address="123 Main St, Atlanta, GA 30301",
    pdf_bytes=dummy_pdf,
    pdf_filename="eviction_notice_test.pdf",
)
print("Client delivery:", "SENT" if ok2 else "FAILED")
