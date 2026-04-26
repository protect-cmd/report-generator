import httpx

GHL_BASE_URL = "https://services.leadconnectorhq.com"


def _auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }


def move_opportunity_stage(api_key: str, opportunity_id: str, stage_id: str) -> None:
    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"
    response = httpx.put(url, headers=_auth_headers(api_key), json={"stageId": stage_id})
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
    response = httpx.post(url, headers=_auth_headers(api_key), json={"body": body})
    response.raise_for_status()
