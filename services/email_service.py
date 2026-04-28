import base64
import logging
import os

import resend

logger = logging.getLogger(__name__)


def _get_client() -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]


def send_sunshine_notification(
    drive_url: str,
    notice_type: str,
    state: str,
    tenant_name: str,
    contact_id: str,
    landlord_name: str | None = None,
    property_address: str | None = None,
    county: str | None = None,
    total_amount_owed: float | None = None,
    reason_for_eviction: str | None = None,
) -> bool:
    """Email Sunshine an internal review link after Drive upload."""
    _get_client()
    from_addr = os.environ.get("RESEND_FROM_ADDRESS", "docs@evictioncommand.com")
    sunshine_email = os.environ["SUNSHINE_EMAIL"]
    admin_email = os.environ["ADMIN_EMAIL"]

    location_id = os.environ.get("GHL_LOCATION_ID", "")
    ghl_profile_url = (
        f"https://app.gohighlevel.com/v2/location/{location_id}/contacts/detail/{contact_id}"
        if location_id else None
    )

    county_display = f"{county} County, " if county else ""
    amount_row = f"<li><strong>Amount owed:</strong> ${total_amount_owed:,.2f}</li>" if total_amount_owed else ""
    reason_row = f"<li><strong>Reason:</strong> {reason_for_eviction}</li>" if reason_for_eviction else ""
    landlord_row = f"<li><strong>Landlord:</strong> {landlord_name}</li>" if landlord_name else ""
    address_row = f"<li><strong>Property:</strong> {property_address} &mdash; {county_display}{state.title()}</li>" if property_address else ""
    profile_link = f"<p><a href='{ghl_profile_url}'>Open contact in GHL</a></p>" if ghl_profile_url else ""

    try:
        resend.Emails.send({
            "from": from_addr,
            "to": [sunshine_email, admin_email],
            "subject": f"[Review Needed] {notice_type} — {tenant_name} ({state.title()})",
            "html": (
                f"<p>A new eviction document is ready for review.</p>"
                f"<ul>"
                f"{landlord_row}"
                f"<li><strong>Tenant:</strong> {tenant_name}</li>"
                f"{address_row}"
                f"<li><strong>Notice type:</strong> {notice_type}</li>"
                f"{amount_row}"
                f"{reason_row}"
                f"</ul>"
                f"<p><a href='{drive_url}'>Open document in Google Drive</a></p>"
                f"{profile_link}"
                f"<p>Approve by adding the <strong>doc-approved</strong> tag in GHL.</p>"
            ),
        })
        logger.info("Sunshine notification sent for contact %s", contact_id)
        return True
    except Exception as exc:
        logger.warning("Sunshine notification failed: %s", exc)
        return False


def send_client_delivery(
    client_email: str,
    client_name: str | None,
    notice_type: str,
    state: str,
    county: str | None,
    property_address: str,
    pdf_bytes: bytes,
    pdf_filename: str,
) -> bool:
    """Email the client their approved eviction document as a PDF attachment."""
    _get_client()
    from_addr = os.environ.get("RESEND_FROM_ADDRESS", "docs@evictioncommand.com")
    phone_display = os.environ.get("EVICTION_COMMAND_PHONE", "")
    county_display = f"{county} County, " if county else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:4px;overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:#0A1628;padding:22px 40px;border-bottom:3px solid #C89B3C;">
              <span style="font-size:18px;font-weight:700;color:#ffffff;letter-spacing:0.2px;">
                Eviction <span style="color:#C89B3C;">Command</span>
              </span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;color:#1a1a1a;font-size:15px;line-height:1.7;">

              <p style="margin:0 0 20px;">Hi {client_name or "there"},</p>
              <p style="margin:0 0 28px;">Your eviction document is ready. Please find it attached to this email.</p>

              <!-- What's attached -->
              <p style="margin:0 0 10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#C89B3C;">What Is Attached</p>
              <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
                <tr><td style="padding:3px 0;color:#1a1a1a;font-size:15px;">&#8212;&nbsp; Your completed {notice_type} prepared for {county_display}{state.title()}</td></tr>
                <tr><td style="padding:3px 0;color:#1a1a1a;font-size:15px;">&#8212;&nbsp; Step-by-step serving instructions for {state.title()}</td></tr>
                <tr><td style="padding:3px 0;color:#1a1a1a;font-size:15px;">&#8212;&nbsp; Important disclaimer &mdash; please read before serving</td></tr>
              </table>

              <!-- Next step -->
              <p style="margin:0 0 10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#C89B3C;">Your Next Step</p>
              <p style="margin:0 0 28px;">Serve the notice to your tenant using the serving instructions attached. Keep a copy of the notice and document exactly when and how you served it. You will need this information if the case goes to court.</p>

              <!-- Divider -->
              <hr style="border:none;border-top:1px solid #e5e5e5;margin:0 0 28px;">

              <!-- Disclaimer -->
              <p style="margin:0 0 10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#0A1628;">Important Reminder</p>
              <p style="margin:0 0 28px;font-size:14px;color:#555555;">Eviction Command is a document preparation service only. We are not attorneys and do not provide legal advice. If your tenant contests the eviction or files a response, we recommend consulting a licensed real estate attorney.</p>

              <p style="margin:0;">Need help? Call us at <strong>{phone_display}</strong> or reply to this email. We are available Monday through Friday 9 AM to 6 PM.</p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#0A1628;padding:20px 40px;">
              <p style="margin:0;font-size:12px;color:rgba(255,255,255,0.5);">The Eviction Command Team &nbsp;&bull;&nbsp; <a href="https://evictioncommand.com" style="color:#C89B3C;text-decoration:none;">evictioncommand.com</a></p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    sunshine_email = os.environ.get("SUNSHINE_EMAIL", "")
    admin_email = os.environ.get("ADMIN_EMAIL", "")
    cc_addresses = [a for a in [sunshine_email, admin_email] if a]

    try:
        payload = {
            "from": from_addr,
            "to": [client_email],
            "subject": f"Your Eviction Document Is Ready — {notice_type} for {property_address}",
            "html": html,
            "attachments": [
                {"filename": pdf_filename, "content": base64.b64encode(pdf_bytes).decode()}
            ],
        }
        if cc_addresses:
            payload["cc"] = cc_addresses
        resend.Emails.send(payload)
        logger.info("Client delivery email sent to %s (cc: %s)", client_email, cc_addresses)
        return True
    except Exception as exc:
        logger.warning("Client delivery email failed: %s", exc)
        return False
