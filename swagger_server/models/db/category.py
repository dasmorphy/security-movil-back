from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Sequence,
    func
)
from swagger_server.models.db import Base


class Category(Base):
    __tablename__ = "category"
    __table_args__ = {"schema": "public"}

    id_category = Column(
        Integer,
        Sequence("category_id_seq", schema="public"),
        primary_key=True,
        nullable=False
    )

    name_category = Column(
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
