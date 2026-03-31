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


class Modules(Base):
    __tablename__ = 'modules'
    __table_args__ = {'schema': 'public'}

    id_module = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )