from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .services.database import Base
from datetime import datetime
from typing import Any


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(primary_key=True)
    device: Mapped[str]
    timestamp: Mapped[datetime]
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)