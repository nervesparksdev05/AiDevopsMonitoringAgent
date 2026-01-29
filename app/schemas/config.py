from typing import List
from pydantic import BaseModel

class EmailConfig(BaseModel):
    enabled: bool
    recipients: List[str]
