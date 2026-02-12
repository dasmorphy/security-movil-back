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


class LogbookOut(Base):
    __tablename__ = 'logbook_out'
    __table_args__ = {'schema': 'public'}

    id_logbook_out = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    unity_id = Column(
        Integer,
        ForeignKey('public.unity_weight.id_unity', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    category_id = Column(
        Integer,
        ForeignKey('public.category.id_category', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    group_business_id = Column(
        Integer,
        ForeignKey('public.group_business.id_group_business', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    shipping_guide = Column(Text)

    quantity = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)

    truck_license = Column(Text)
    name_driver = Column(Text)
    name_user = Column(Text)
    person_withdraws = Column(Text)
    destiny = Column(Text)
    authorized_by = Column(Text)
    observations = Column(Text)
    workday = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    created_by = Column(Text, nullable=False)
    updated_by = Column(Text, nullable=False)


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

