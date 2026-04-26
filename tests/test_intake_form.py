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

REQUIRED_FIELDS = [
    "contact_id", "opportunity_id", "full_name", "email", "phone",
    "property_address", "city", "state", "county",
    "tenant_full_legal_name", "notice_type",
]

EXPECTED_KEYS = {
    "contact_id", "opportunity_id", "full_name", "email", "phone",
    "best_time_to_reach", "property_address", "city", "state", "county",
    "property_type", "tenant_full_legal_name", "additional_tenants",
    "tenant_phone", "lease_start_date", "lease_end_date", "month_to_month",
    "monthly_rent", "security_deposit", "notice_type", "reason_for_eviction",
    "total_amount_owed", "date_rent_last_paid", "months_unpaid",
    "describe_violation", "prior_notices", "prior_notices_description",
    "rent_control", "additional_notes",
}


def test_valid_payload_parses():
    form = IntakeForm(**VALID_PAYLOAD)
    assert form.contact_id == "abc123"
    assert form.state == "Georgia"
    assert form.notice_type == "3-Day Pay or Quit"
    assert form.monthly_rent == 1500


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_missing_required_field_raises(field):
    payload = {**VALID_PAYLOAD}
    del payload[field]
    with pytest.raises(ValidationError):
        IntakeForm(**payload)


def test_empty_string_optional_fields_become_none():
    form = IntakeForm(**VALID_PAYLOAD)
    # VALID_PAYLOAD has "" for these — validator should convert to None
    assert form.additional_tenants is None
    assert form.tenant_phone is None
    assert form.lease_end_date is None
    assert form.describe_violation is None
    assert form.additional_notes is None


def test_absent_optional_fields_default_to_none():
    payload = {**VALID_PAYLOAD}
    del payload["additional_tenants"]
    del payload["tenant_phone"]
    form = IntakeForm(**payload)
    assert form.additional_tenants is None
    assert form.tenant_phone is None


def test_invalid_email_raises():
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}
    with pytest.raises(ValidationError):
        IntakeForm(**payload)


def test_to_dict_returns_all_fields():
    form = IntakeForm(**VALID_PAYLOAD)
    assert form.model_dump().keys() == EXPECTED_KEYS
