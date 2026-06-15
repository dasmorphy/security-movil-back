from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Text,
    ForeignKey,
    func
)


class EmployeeMovement(Base):
    __tablename__ = 'employee_movements'
    __table_args__ = {'schema': 'public'}

    id_movement = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_id = Column(
        Integer,
        ForeignKey(
            'public.employees_intern.id_employee',
            onupdate='NO ACTION',
            ondelete='NO ACTION'
        )
    )

    group_business_id = Column(
        Integer,
        ForeignKey(
            'public.group_business.id_group_business',
            onupdate='NO ACTION',
            ondelete='NO ACTION'
        )
    )

    destiny_id = Column(
        Integer,
        ForeignKey(
            'public.group_business.id_group_business',
            onupdate='NO ACTION',
            ondelete='NO ACTION'
        )
    )

    authorized_id = Column(
        Integer,
        ForeignKey(
            'public.authorized.id_authorized',
            onupdate='NO ACTION',
            ondelete='NO ACTION'
        )
    )

    type_movement = Column(Text)
    shipping_guide = Column(Text)
    observations = Column(Text)
    other_destiny = Column(Text)
    reason_out = Column(Text)
    name_user = Column(Text)

    created_by = Column(Text)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_by = Column(Text)

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    def to_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }