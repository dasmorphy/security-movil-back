from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func
)


class StatusPurchaseOrder(Base):
    __tablename__ = 'status_purchase_orders'
    __table_args__ = {'schema': 'public'}

    id_status = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    created_by = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
