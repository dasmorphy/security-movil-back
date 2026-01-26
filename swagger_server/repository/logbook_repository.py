

from typing import List
from loguru import logger
from sqlalchemy import exists, func, insert, select
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.category import Category
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.resources.databases.postgresql import PostgreSQLClient


class LogbookRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")


    def post_logbook_entry(self, logbook_entry_body: LogbookEntry, internal, external) -> None:
        with self.db.session_factory() as session:
            try:

                # 🔎 validar si existe la categoría
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
                
                new_logbook = insert(LogbookEntry).values(
                    unity_id=logbook_entry_body.unity_id,
                    category_id=logbook_entry_body.category_id,
                    shipping_guide=logbook_entry_body.shipping_guide,
                    description=logbook_entry_body.description,
                    quantity=logbook_entry_body.quantity,
                    weight=logbook_entry_body.weight,
                    provider=logbook_entry_body.provider,
                    destiny_intern=logbook_entry_body.destiny_intern,
                    authorized_by=logbook_entry_body.authorized_by,
                    observations=logbook_entry_body.observations,
                    created_by=logbook_entry_body.created_by,
                    updated_by=logbook_entry_body.created_by
                )

                session.execute(new_logbook)
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()


    def post_logbook_out(self, logbook_entry_body: LogbookEntry, internal, external) -> None:
        with self.db.session_factory() as session:
            try:

                # 🔎 validar si existe la categoría
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
                
                new_logbook = insert(LogbookEntry).values(
                    unity_id=logbook_entry_body.unity_id,
                    category_id=logbook_entry_body.category_id,
                    shipping_guide=logbook_entry_body.shipping_guide,
                    description=logbook_entry_body.description,
                    quantity=logbook_entry_body.quantity,
                    weight=logbook_entry_body.weight,
                    provider=logbook_entry_body.provider,
                    destiny_intern=logbook_entry_body.destiny_intern,
                    authorized_by=logbook_entry_body.authorized_by,
                    observations=logbook_entry_body.observations,
                    created_by=logbook_entry_body.created_by,
                    updated_by=logbook_entry_body.created_by
                )

                session.execute(new_logbook)
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