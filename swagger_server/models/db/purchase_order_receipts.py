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

    logbook_entry_id = Column(
        Integer,
        ForeignKey('public.logbook_entry.id_logbook_entry', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    converted_amount = Column(Numeric(12, 3))
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
