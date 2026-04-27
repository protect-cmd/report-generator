import httpx

GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_TIMEOUT_SECONDS = 10.0


def _auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }



def move_opportunity_stage(
    api_key: str,
    contact_id: str,
    pipeline_id: str,
    stage_id: str,
    location_id: str,
) -> None:
    url = f"{GHL_BASE_URL}/opportunities/upsert"
    body = {
        "contactId": contact_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": stage_id,
        "locationId": location_id,
    }
    response = httpx.post(url, headers=_auth_headers(api_key), json=body, timeout=GHL_TIMEOUT_SECONDS)
    if not response.is_success:
        import logging
        logging.getLogger(__name__).error("GHL upsert — status=%s body=%s", response.status_code, response.text)
        raise ValueError(f"GHL {response.status_code}")


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
