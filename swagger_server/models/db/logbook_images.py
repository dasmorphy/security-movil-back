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


class LogbookImages(Base):
    __tablename__ = 'logbook_images'
    __table_args__ = {'schema': 'public'}

    id_image = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    logbook_id_entry = Column(
        Integer,
        ForeignKey('public.logbook_entry.id_logbook_entry', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    logbook_id_out = Column(
        Integer,
        ForeignKey('public.logbook_out.id_logbook_out', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    image_path = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )
