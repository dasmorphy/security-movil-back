import uuid
from sqlalchemy import (
    Column,
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


class Roles(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "public"}

    id_rol = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    name = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now()
    )