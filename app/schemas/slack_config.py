from pydantic import BaseModel

class SlackConfig(BaseModel):
    enabled: bool
    webhook_url: str
