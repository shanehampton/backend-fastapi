from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid


class BaseModel(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        sort_order=-1  # force as first column in db table
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(tz=timezone.utc)
    )
