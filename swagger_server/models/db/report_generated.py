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


class ReportGenerated(Base):
    __tablename__ = 'report_generated'
    __table_args__ = {'schema': 'public'}

    id_report = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    business_id = Column(
        Integer,
        ForeignKey('public.business.id_business', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    type_report = Column(Text)
    status = Column(Text)
    shipping_error = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    start_date = Column(
        DateTime
    )

    deadline = Column(
        DateTime
    )

    shipping_date = Column(
        DateTime
    )

    created_by = Column(Text, nullable=False)
