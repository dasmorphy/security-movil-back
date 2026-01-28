from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Time,
    ForeignKey,
    func
)


class Business(Base):
    __tablename__ = 'business'
    __table_args__ = {'schema': 'public'}

    id_business = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )