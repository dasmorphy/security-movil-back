from swagger_server.models.db import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func
)


class ApplicationChannels(Base):
    __tablename__ = 'application_channels'
    __table_args__ = {'schema': 'public'}

    id_channel = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    channel = Column(Text)
    platform = Column(Text)
    application = Column(Text)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    created_by = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
