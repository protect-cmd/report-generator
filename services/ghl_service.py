import httpx

GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_TIMEOUT_SECONDS = 10.0


def _auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }


def get_opportunity_id(api_key: str, contact_id: str, location_id: str) -> str:
    """Look up the most recent opportunity for a contact by contact_id."""
    url = f"{GHL_BASE_URL}/opportunities/search"
    params = {"contact_id": contact_id, "location_id": location_id}
    response = httpx.get(url, headers=_auth_headers(api_key), params=params, timeout=GHL_TIMEOUT_SECONDS)
    response.raise_for_status()
    opportunities = response.json().get("opportunities", [])
    if not opportunities:
        raise ValueError(f"No opportunity found for contact {contact_id}")
    return opportunities[0]["id"]


def move_opportunity_stage(api_key: str, opportunity_id: str, stage_id: str) -> None:
    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"
    response = httpx.put(url, headers=_auth_headers(api_key), json={"stageId": stage_id}, timeout=GHL_TIMEOUT_SECONDS)
    response.raise_for_status()


def update_contact_custom_field(api_key: str, contact_id: str, field_key: str, value: str) -> None:
    url = f"{GHL_BASE_URL}/contacts/{contact_id}"
    response = httpx.put(
        url,
        headers=_auth_headers(api_key),
        json={"customFields": [{"key": field_key, "field_value": value}]},
        timeout=GHL_TIMEOUT_SECONDS,
    )
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
    response = httpx.post(url, headers=_auth_headers(api_key), json={"body": body}, timeout=GHL_TIMEOUT_SECONDS)
    response.raise_for_status()
