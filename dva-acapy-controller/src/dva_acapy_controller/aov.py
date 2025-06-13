from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel


class AOV(BaseModel):
    vc_id: str
    valid_since: datetime
    subject: str
    issuer_id: str
    record_id: str
    contract_id: str
    payload: str


class AOVRequest(BaseModel):
    subject: str
    issuer_id: str
    payload: Dict[str, Any]
    target: str = "self"

