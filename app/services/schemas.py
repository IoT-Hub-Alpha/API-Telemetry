from pydantic import BaseModel
from datetime import datetime
from typing import Any


class TelemetryResponse(BaseModel):
    id: int
    device: str
    timestamp: datetime
    payload: dict[str, Any]

    model_config = {"from_attributes": True}
