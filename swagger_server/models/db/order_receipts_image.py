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


class OrderReceiptsImages(Base):
    __tablename__ = 'order_receipts_images'
    __table_args__ = {'schema': 'public'}

    id_image = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    order_receipt_id = Column(
        Integer,
        ForeignKey('public.purchase_order_receipts.id_receipts', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    image_path = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )
