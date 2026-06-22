from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func
)


class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    __table_args__ = {'schema': 'public'}

    id_order = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    status_id = Column(
        Integer,
        ForeignKey('public.status_purchase_orders.id_status', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    destiny_id = Column(
        Integer,
        ForeignKey('public.status_purchase_orders.id_status', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    start_date = Column(DateTime)
    end_date = Column(DateTime)

    number_order = Column(Text)
    type_order = Column(Text)
    quantity = Column(Integer)
    provider = Column(Text)
    observations = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    created_by = Column(Text)
    updated_by = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
