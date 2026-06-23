from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func
)


class ReasonRestriction(Base):
    __tablename__ = 'reason_restriction'
    __table_args__ = {'schema': 'public'}

    id_reason = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    reason = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    created_by = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
