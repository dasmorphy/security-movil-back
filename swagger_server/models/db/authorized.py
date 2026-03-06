from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Sequence,
    String,
    Text,
    Time,
    ForeignKey,
    func
)


class Authorized(Base):
    __tablename__ = 'authorized'
    __table_args__ = {'schema': 'public'}

    id_authorized = Column(
        Integer,
        Sequence("authorized_id_seq", schema="public"),
        primary_key=True,
        nullable=False
    )

    name = Column(Text, nullable=False)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )