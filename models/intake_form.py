from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, model_validator


def _null_str(v):
    """Return None if value is the literal string 'null', empty, or actual None."""
    if v is None:
        return None
    if isinstance(v, str) and v.strip().lower() in ("null", ""):
        return None
    return v


class IntakeForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # Required fields
    contact_id: str
    opportunity_id: Optional[str] = None
    full_name: Optional[str] = None
    email: EmailStr
    phone: str
    property_address: str
    city: str
    state: str
    county: Optional[str] = None
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

    @model_validator(mode="before")
    @classmethod
    def normalize_null_strings(cls, data):
        """Convert GHL's literal 'null' strings to None before field validation."""
        if not isinstance(data, dict):
            return data
        str_fields = {
            "opportunity_id", "full_name", "county", "best_time_to_reach",
            "property_type", "additional_tenants", "tenant_phone",
            "lease_start_date", "lease_end_date", "reason_for_eviction",
            "date_rent_last_paid", "describe_violation", "prior_notices",
            "prior_notices_description", "rent_control", "additional_notes",
        }
        for field in str_fields:
            if field in data:
                data[field] = _null_str(data[field])

        # Coerce numeric string fields; treat "null" as None
        for field in ("monthly_rent", "security_deposit", "total_amount_owed"):
            v = _null_str(data.get(field))
            if v is not None:
                try:
                    data[field] = float(v)
                except (ValueError, TypeError):
                    data[field] = None
            else:
                data[field] = None

        v = _null_str(data.get("months_unpaid"))
        if v is not None:
            try:
                data["months_unpaid"] = int(float(v))
            except (ValueError, TypeError):
                data["months_unpaid"] = None
        else:
            data["months_unpaid"] = None

        # month_to_month: GHL sends "null", "true", "false", or actual bool
        v = _null_str(data.get("month_to_month"))
        if v is None:
            data["month_to_month"] = None
        elif isinstance(v, bool):
            pass
        elif isinstance(v, str):
            data["month_to_month"] = v.lower() in ("true", "1", "yes")

        return data
