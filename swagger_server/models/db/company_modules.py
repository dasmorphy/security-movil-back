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


class CompanyModules(Base):
    __tablename__ = 'company_modules'
    __table_args__ = {'schema': 'public'}

    id_company_module = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    business_id = Column(
        Integer,
        ForeignKey('public.business.id_business', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    module_id = Column(
        Integer,
        ForeignKey('public.modules.id_module', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )