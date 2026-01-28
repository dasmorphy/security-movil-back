

from typing import List
from loguru import logger
from sqlalchemy import exists, func, insert, select
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.category import Category
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.resources.databases.postgresql import PostgreSQLClient
from swagger_server.utils.utils import get_date_range


class LogbookRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")


    def post_logbook_entry(self, logbook_entry_body: LogbookEntry, internal, external) -> None:
        with self.db.session_factory() as session:
            try:
                category_exists = session.execute(
                    select(
                        exists().where(
                            Category.id_category == logbook_entry_body.category_id
                        )
                    )
                ).scalar()

                unity_weight_exists = session.execute(
                    select(
                        exists().where(
                            UnityWeight.id_unity == logbook_entry_body.unity_id
                        )
                    )
                ).scalar()

                if not category_exists:
                    raise CustomAPIException(
                        message="No existe la categoría",
                        status_code=404
                    )
                
                if not unity_weight_exists:
                    raise CustomAPIException(
                        message="No existe la unidad de peso",
                        status_code=404
                    )
                
                session.add(logbook_entry_body)
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()

    def post_logbook_out(self, logbook_out_body: LogbookOut, internal, external) -> None:
        with self.db.session_factory() as session:
            try:
                unity_weight_exists = True
                category_exists = session.execute(
                    select(
                        exists().where(
                            Category.id_category == logbook_out_body.category_id
                        )
                    )
                ).scalar()

                #Si no viene unity_id, buscar la unidad por defecto (LB)
                if not logbook_out_body.unity_id:
                    unity_weight = session.execute(
                        select(UnityWeight)
                        .where(UnityWeight.code == 'LB')
                    ).scalar_one_or_none()

                    if not unity_weight:
                        raise CustomAPIException(
                            message="No existe la unidad de peso por defecto (LB)",
                            status_code=404
                        )

                    logbook_out_body.unity_id = unity_weight.id_unity

                else:
                    #validar si existe la unidad enviada
                    unity_weight_exists = session.execute(
                        select(
                            exists().where(
                                UnityWeight.id_unity == logbook_out_body.unity_id
                            )
                        )
                    ).scalar()

                    if not unity_weight_exists:
                        raise CustomAPIException(
                            message="No existe la unidad de peso",
                            status_code=404
                        )

                if not category_exists:
                    raise CustomAPIException(
                        message="No existe la categoría",
                        status_code=404
                    )
                
                if not unity_weight_exists:
                    raise CustomAPIException(
                        message="No existe la unidad de peso",
                        status_code=404
                    )
                
                session.add(logbook_out_body)
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()

    def get_all_categories(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(Category)
                )
                categories = [
                    {
                        "id_category": c.id_category,
                        "name_category": c.name_category,
                        "code": c.code,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    }
                    for c in result.scalars().all()
                ]
                return categories
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_all_unities(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(UnityWeight)
                )
                categories = [
                    {
                        "id_unity": c.id_unity,
                        "name": c.name,
                        "code": c.code,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    }
                    for c in result.scalars().all()
                ]
                return categories
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_logbook_resume(self, internal, external, model: LogbookOut | LogbookEntry, fecha_inicio=None, fecha_fin=None):
        with self.db.session_factory() as session:
            start, end = get_date_range(fecha_inicio, fecha_fin)
            try:
                return (
                    session.query(
                        Category.id_category,
                        Category.name_category,
                        func.sum(model.quantity).label("cantidad"),
                        UnityWeight.name.label("unidad"),
                    )
                    .join(Category, Category.id_category == model.category_id)
                    .join(UnityWeight, UnityWeight.id_unity == model.unity_id)
                    .filter(model.created_at >= start)
                    .filter(model.created_at < end)
                    .group_by(
                        Category.id_category,
                        Category.name_category,
                        UnityWeight.name,
                    )
                    .order_by(Category.name_category)
                    .all()
                )
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)