from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Text,
    Time,
    Sequence,
    func
)

from swagger_server.models.db import Base


class UnityWeight(Base):
    __tablename__ = "unity_weight"
    __table_args__ = {"schema": "public"}

    id_unity = Column(
        Integer,
        Sequence("unity_weight_id_seq", schema="public"),
        primary_key=True,
        nullable=False
    )

    name = Column(
        Text,
        nullable=False
    )

    code = Column(
        Text,
        nullable=False
    )

    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )
