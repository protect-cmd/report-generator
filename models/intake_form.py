from typing import Optional
from pydantic import BaseModel


class IntakeForm(BaseModel):
    contact_id: str
    opportunity_id: str
    full_name: str
    email: str
    phone: str
    best_time_to_reach: Optional[str] = None
    property_address: str
    city: str
    state: str
    county: str
    property_type: Optional[str] = None
    tenant_full_legal_name: str
    additional_tenants: Optional[str] = None
    tenant_phone: Optional[str] = None
    lease_start_date: Optional[str] = None
    lease_end_date: Optional[str] = None
    month_to_month: Optional[bool] = None
    monthly_rent: Optional[float] = None
    security_deposit: Optional[float] = None
    notice_type: str
    reason_for_eviction: Optional[str] = None
    total_amount_owed: Optional[float] = None
    date_rent_last_paid: Optional[str] = None
    months_unpaid: Optional[int] = None
    describe_violation: Optional[str] = None
    prior_notices: Optional[str] = None
    prior_notices_description: Optional[str] = None
    rent_control: Optional[str] = None
    additional_notes: Optional[str] = None
