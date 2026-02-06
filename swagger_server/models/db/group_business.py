from swagger_server.models.db import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Time,
    ForeignKey,
    func
)


class GroupBusiness(Base):
    __tablename__ = 'group_business'
    __table_args__ = {'schema': 'public'}

    id_group_business = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    sector_id = Column(
        Integer,
        ForeignKey('public.sector.id_sector', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    business_id = Column(
        Integer,
        ForeignKey('public.business.id_business', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    name = Column(Text)

    is_active = Column(Boolean, default=True)

    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )