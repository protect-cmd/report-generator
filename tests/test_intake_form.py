import pytest
from pydantic import ValidationError
from models.intake_form import IntakeForm


VALID_PAYLOAD = {
    "contact_id": "abc123",
    "opportunity_id": "opp456",
    "full_name": "John Smith",
    "email": "john@example.com",
    "phone": "5551234567",
    "best_time_to_reach": "Morning",
    "property_address": "123 Main St Unit 4",
    "city": "Atlanta",
    "state": "Georgia",
    "county": "Fulton",
    "property_type": "Single Family Home",
    "tenant_full_legal_name": "Jane Doe",
    "additional_tenants": "",
    "tenant_phone": "",
    "lease_start_date": "2023-01-01",
    "lease_end_date": "",
    "month_to_month": True,
    "monthly_rent": 1500,
    "security_deposit": 1500,
    "notice_type": "3-Day Pay or Quit",
    "reason_for_eviction": "Nonpayment of Rent",
    "total_amount_owed": 3000,
    "date_rent_last_paid": "2024-10-01",
    "months_unpaid": 2,
    "describe_violation": "",
    "prior_notices": "Yes",
    "prior_notices_description": "Verbal warning in October",
    "rent_control": "Not Sure",
    "additional_notes": "",
}


def test_valid_payload_parses():
    form = IntakeForm(**VALID_PAYLOAD)
    assert form.contact_id == "abc123"
    assert form.state == "Georgia"
    assert form.notice_type == "3-Day Pay or Quit"
    assert form.monthly_rent == 1500


def test_missing_required_field_raises():
    payload = {**VALID_PAYLOAD}
    del payload["contact_id"]
    with pytest.raises(ValidationError):
        IntakeForm(**payload)


def test_optional_fields_default_to_none_or_empty():
    payload = {**VALID_PAYLOAD}
    del payload["additional_tenants"]
    del payload["tenant_phone"]
    del payload["describe_violation"]
    del payload["additional_notes"]
    form = IntakeForm(**payload)
    assert form.additional_tenants is None or form.additional_tenants == ""
    assert form.tenant_phone is None or form.tenant_phone == ""


def test_to_dict_returns_all_fields():
    form = IntakeForm(**VALID_PAYLOAD)
    d = form.model_dump()
    assert "full_name" in d
    assert "tenant_full_legal_name" in d
    assert "notice_type" in d
