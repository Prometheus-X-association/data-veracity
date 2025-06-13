import uuid
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel

"""
https://docs.pydantic.dev/latest/api/base_model/
"""
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