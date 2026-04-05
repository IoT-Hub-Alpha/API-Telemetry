from datetime import datetime
from typing import Any
from sqlalchemy import Index, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(primary_key=True)
    device: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        Index(
            "idx_telemetry_device_time",
            "device",
            timestamp.desc(),
        ),
        Index(
            "idx_telemetry_payload_gin",
            "payload",
            postgresql_using="gin",
        ),
    )
