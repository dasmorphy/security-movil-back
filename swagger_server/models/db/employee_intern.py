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


class EmployeeIntern(Base):
    __tablename__ = 'employees_intern'
    __table_args__ = {'schema': 'public'}

    id_employee = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dni = Column(Text)
    names = Column(Text)
    lastname = Column(Text)
    position = Column(Text)
    observations = Column(Text)
    name_user = Column(Text)
    photo = Column(Text)
    status = Column(Text)
    created_by = Column(Text)

    group_business_id = Column(
        Integer,
        ForeignKey('public.group_business.id_group_business', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )
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
