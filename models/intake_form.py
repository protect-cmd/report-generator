from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class IntakeForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # Required fields
    contact_id: str
    opportunity_id: str
    full_name: str
    email: EmailStr
    phone: str
    property_address: str
    city: str
    state: str
    county: str
    tenant_full_legal_name: str
    notice_type: str

    # Optional fields
    best_time_to_reach: Optional[str] = None
    property_type: Optional[str] = None
    additional_tenants: Optional[str] = None
    tenant_phone: Optional[str] = None
    lease_start_date: Optional[str] = None
    lease_end_date: Optional[str] = None
    month_to_month: Optional[bool] = None
    monthly_rent: Optional[float] = None
    security_deposit: Optional[float] = None
    reason_for_eviction: Optional[str] = None
    total_amount_owed: Optional[float] = None
    date_rent_last_paid: Optional[str] = None
    months_unpaid: Optional[int] = None
    describe_violation: Optional[str] = None
    prior_notices: Optional[str] = None
    prior_notices_description: Optional[str] = None
    rent_control: Optional[str] = None
    additional_notes: Optional[str] = None

    @field_validator(
        "lease_start_date", "lease_end_date", "date_rent_last_paid",
        "additional_tenants", "tenant_phone", "describe_violation",
        "additional_notes", "prior_notices_description",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
