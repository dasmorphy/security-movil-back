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


class DestinyIntern(Base):
    __tablename__ = 'destiny_intern'
    __table_args__ = {'schema': 'public'}

    id_destiny = Column(
        Integer,
        Sequence("destiny_id_seq", schema="public"),
        primary_key=True,
        nullable=False
    )

    name = Column(Text)

    business_id = Column(
        Integer,
        ForeignKey('public.business.id_business', onupdate='NO ACTION', ondelete='NO ACTION'),
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