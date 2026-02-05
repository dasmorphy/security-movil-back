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


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "public"}

    id_role_permission = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.roles.id_rol", onupdate="NO ACTION", ondelete="NO ACTION"),
        nullable=False
    )

    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.permissions.id_permission", onupdate="NO ACTION", ondelete="NO ACTION"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now()
    )