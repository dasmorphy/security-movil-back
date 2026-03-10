import uuid
from sqlalchemy import (
    Column,
    Sequence,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from swagger_server.models.db import Base


class RequestIdempotency(Base):
    __tablename__ = "request_idempotency"
    __table_args__ = {"schema": "public"}

    id_request = Column(
        Sequence("request_idempotency_id_seq", schema="public"),
        primary_key=True,
        nullable=False
    )

    uuid = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
    )

    endpoint = Column(Text)

    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now()
    )