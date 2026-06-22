from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func
)


class PurchaseOrderReceipts(Base):
    __tablename__ = 'purchase_order_receipts'
    __table_args__ = {'schema': 'public'}

    id_receipts = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    purchase_order_id = Column(
        Integer,
        ForeignKey('public.purchase_orders.id_order', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    dni_driver = Column(Text)
    truck_license = Column(Text)
    driver = Column(Text)
    quantity = Column(Integer)
    tons_equivalent = Column(Integer)
    
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
