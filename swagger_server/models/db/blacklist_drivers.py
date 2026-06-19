from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Text,
    func
)


class BlacklistDrivers(Base):
    __tablename__ = 'blacklist_drivers'
    __table_args__ = {'schema': 'public'}

    id_blacklist = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dni = Column(Text)
    full_names = Column(Text)
    reason_restriction = Column(Text)
    observations = Column(Text)
    image_path = Column(Text)
    
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
