from typing import Optional
from pydantic import BaseModel, EmailStr


class DeliverRequest(BaseModel):
    contact_id: str
    email: EmailStr
    full_name: Optional[str] = None
    notice_type: str
    state: str
    county: Optional[str] = None
    property_address: str
    drive_url: str
