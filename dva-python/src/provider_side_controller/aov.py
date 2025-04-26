import uuid
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel


class Evaluation(BaseModel):
    eval: List[Dict[str, Any]] = []

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
    evaluations: Evaluation