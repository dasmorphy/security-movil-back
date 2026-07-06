from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func
)


class PurchaseOrderDestinations(Base):
    __tablename__ = 'purchase_order_destinations'
    __table_args__ = {'schema': 'public'}

    id_purchase_destiny = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    order_id = Column(
        Integer,
        ForeignKey('public.purchase_orders.id_order', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    destiny_id = Column(
        Integer,
        ForeignKey('public.status_purchase_orders.id_status', onupdate='NO ACTION', ondelete='NO ACTION'),
    )
        
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    created_by = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
