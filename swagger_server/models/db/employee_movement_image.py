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


class EmployeeMovementImage(Base):
    __tablename__ = 'employee_movements_images'
    __table_args__ = {'schema': 'public'}

    id_image = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_movement_id = Column(
        Integer,
        ForeignKey('public.employee_movements.id_movement', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    image_path = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )
