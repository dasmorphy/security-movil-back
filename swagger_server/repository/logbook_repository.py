

from datetime import datetime, timedelta
from typing import List
from unittest import result
from flask import json
from loguru import logger
from sqlalchemy import ARRAY, DateTime, Integer, String, Text, and_, cast, exists, func, insert, literal, select, true, union_all
from sqlalchemy.orm import aliased
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.authorized import Authorized
from swagger_server.models.db.business import Business
from swagger_server.models.db.business import Business
from swagger_server.models.db.destiny_intern import DestinyIntern
from swagger_server.models.db.group_business import GroupBusiness
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.category import Category
from swagger_server.models.db.logbook_images import LogbookImages
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.db.report_generated import ReportGenerated
from swagger_server.models.db.request_idempotency import RequestIdempotency
from swagger_server.models.db.sector import Sector
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.resources.databases import postgresql
from swagger_server.resources.databases.postgresql import PostgreSQLClient
from swagger_server.resources.databases.redis import RedisClient
from swagger_server.utils.utils import SEARCH_COLUMNS_ENTRY, SEARCH_COLUMNS_OUT, apply_search, get_date_range, parse_filters
import os
from PIL import Image
from uuid import uuid4
from werkzeug.utils import secure_filename
import getpass
from sqlalchemy.dialects import postgresql

class LogbookRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")
        self.redis_client = RedisClient()


    def post_logbook_entry(self, logbook_entry_body: LogbookEntry, images, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/post/logbook-entry"
                )
                
                self.request_idempotency(session, data_request, internal, external)

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

                group_business_exists = session.execute(
                    select(GroupBusiness).where(
                        GroupBusiness.id_group_business == logbook_entry_body.group_business_id
                    )
                ).scalar_one_or_none()

                category = session.execute(
                    select(Category).where(
                        Category.id_category == logbook_entry_body.category_id
                    )
                ).scalar_one_or_none()

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
                
                if not group_business_exists:
                    raise CustomAPIException(
                        message="No existe el grupo de negocio",
                        status_code=404
                    )
                
                session.add(logbook_entry_body)
                session.flush()
                
                logbook_entry_id = logbook_entry_body.id_logbook_entry

                #Guardar imágenes (máx 10)
                for file in images[:10]:
                    result = self.save_image(file)
                    saved_files.append(result["url"])

                    image = LogbookImages(
                        logbook_id_entry=logbook_entry_id,
                        image_path=result["url"]
                    )

                    session.add(image)

                session.commit()

                logbook_entry_dict = logbook_entry_body.to_dict()
                logbook_entry_dict["name_category"] = category.name_category
                logbook_entry_dict["group_name"] = group_business_exists.name

                self.redis_client.client.publish(
                    "logbook_channel",
                    json.dumps({
                        "type": "logbook_saved",
                        "logbook": logbook_entry_dict
                    })
                )

            except OSError as e:
                if e.errno == 36:
                    raise CustomAPIException("Nombre de archivo demasiado largo", 400)

            except Exception as exception:
                session.rollback()

                #limpia archivos guardados si falla DB
                for path in saved_files:
                    full_path = os.path.join("/var/www", path.lstrip("/"))
                    if os.path.exists(full_path):
                        os.remove(full_path)

                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()

    def post_logbook_out(self, logbook_out_body: LogbookOut, images, id_logbook_entry, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/post/logbook-out"
                )
                
                self.request_idempotency(session, data_request, internal, external)

                unity_weight_exists = True
                category_exists = session.execute(
                    select(
                        exists().where(
                            Category.id_category == logbook_out_body.category_id
                        )
                    )
                ).scalar()

                group_business_exists = session.execute(
                    select(GroupBusiness).where(
                        GroupBusiness.id_group_business == logbook_out_body.group_business_id
                    )
                ).scalar_one_or_none()

                category = session.execute(
                    select(Category).where(
                        Category.id_category == logbook_out_body.category_id
                    )
                ).scalar_one_or_none()

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
                
                if not group_business_exists:
                    raise CustomAPIException(
                        message="No existe el grupo de negocio",
                        status_code=404
                    )
                
                session.add(logbook_out_body)
                session.flush()
                
                logbook_out_id = logbook_out_body.id_logbook_out

                if id_logbook_entry: 
                    logbook_entry = session.get(LogbookEntry, id_logbook_entry)
                    
                    if not logbook_entry:
                        raise CustomAPIException(
                            message="No existe el id de la bitacora de ingreso relacionado",
                            status_code=404
                        )
                    
                    logbook_entry.logbook_out_id = logbook_out_id
                    logbook_entry.updated_by = logbook_out_body.created_by
                    logbook_entry.updated_at = datetime.now()
                    logbook_entry.status = "Finalizado"

                # Guardar imágenes (máx 10)
                for file in images[:10]:
                    result = self.save_image(file)
                    saved_files.append(result["url"])

                    image = LogbookImages(
                        logbook_id_out=logbook_out_id,
                        image_path=result["url"]
                    )

                    session.add(image)

                session.commit()

                logbook_out_dict = logbook_out_body.to_dict()
                logbook_out_dict["name_category"] = category.name_category
                logbook_out_dict["group_name"] = group_business_exists.name

                self.redis_client.client.publish(
                    "logbook_channel",
                    json.dumps({
                        "type": "logbook_saved",
                        "logbook": logbook_out_dict
                    })
                )


            except OSError as e:
                if e.errno == 36:
                    raise CustomAPIException("Nombre de archivo demasiado largo", 400)
                
            except Exception as exception:
                session.rollback()

                #limpia archivos guardados si falla DB
                for path in saved_files:
                    full_path = os.path.join("/var/www", path.lstrip("/"))
                    if os.path.exists(full_path):
                        os.remove(full_path)

                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()

    def delete_logbook(self, params, internal, external):
        id_logbook_delete = params.get('id-logbook')
        type_logbook_delete = params.get('type-logbook')

        with self.db.session_factory() as session:
            try:

                if type_logbook_delete == 'entrada':

                    # 🔹 Obtener entrada real
                    logbook_entry = session.execute(
                        select(LogbookEntry).where(
                            LogbookEntry.id_logbook_entry == id_logbook_delete
                        )
                    ).scalar_one_or_none()

                    if not logbook_entry:
                        raise CustomAPIException(
                            message="No existe la bitacora de entrada",
                            status_code=404
                        )

                    # 🔥 Si tiene salida asociada → desvincular primero
                    if logbook_entry.logbook_out_id:

                        logbook_out_id = logbook_entry.logbook_out_id

                        # ✅ Romper la FK
                        logbook_entry.logbook_out_id = None
                        session.flush()  # 🔥 CLAVE

                        # Eliminar imágenes de salida
                        session.query(LogbookImages).filter(
                            LogbookImages.logbook_id_out == logbook_out_id
                        ).delete(synchronize_session=False)

                        # Eliminar salida
                        session.query(LogbookOut).filter(
                            LogbookOut.id_logbook_out == logbook_out_id
                        ).delete(synchronize_session=False)

                    # Eliminar imágenes de entrada
                    session.query(LogbookImages).filter(
                        LogbookImages.logbook_id_entry == id_logbook_delete
                    ).delete(synchronize_session=False)

                    # Eliminar entrada
                    session.delete(logbook_entry)

                    session.commit()

                elif type_logbook_delete == 'salida':

                    # 🔹 Obtener salida real
                    logbook_out = session.execute(
                        select(LogbookOut).where(
                            LogbookOut.id_logbook_out == id_logbook_delete
                        )
                    ).scalar_one_or_none()

                    if not logbook_out:
                        raise CustomAPIException(
                            message="No existe la bitacora de salida",
                            status_code=404
                        )

                    # 🔥 Desvincular entradas que apunten a esta salida
                    session.query(LogbookEntry).filter(
                        LogbookEntry.logbook_out_id == id_logbook_delete
                    ).update({
                        "logbook_out_id": None
                    })

                    # Eliminar imágenes de salida
                    session.query(LogbookImages).filter(
                        LogbookImages.logbook_id_out == id_logbook_delete
                    ).delete()

                    # Eliminar salida
                    session.delete(logbook_out)

                    session.commit()

                else:
                    raise CustomAPIException(
                        message="Tipo de bitacora no existe",
                        status_code=404
                    )

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)

                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error en la base de datos", 500)

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
            
    def get_all_sectores(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(Sector)
                )
                sectors = [
                    {
                        "id_sector": c.id_sector,
                        "name": c.name,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    }
                    for c in result.scalars().all()
                ]
                return sectors
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_all_authorized(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(Authorized)
                )
                authorized = [
                    {
                        "id_authorized": c.id_authorized,
                        "name": c.name,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    }
                    for c in result.scalars().all()
                ]
                return authorized
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            

    def get_all_destiny(self, business, internal, external):
        with self.db.session_factory() as session:
            try:
                logger.info('get_all_destiny | business recibido: {} | type: {}', 
                        repr(business), type(business).__name__, 
                        internal=internal, external=external)

                stmt = select(DestinyIntern)

                # Caso 1: no viene business → default = 1
                if not business:
                    logger.info('get_all_destiny | CASO 1: business vacío, filtrando por business_id=1',
                            internal=internal, external=external)
                    stmt = stmt.where(DestinyIntern.business_id == 1)

                # Caso 2: viene business distinto de Telearseg → filtrar
                elif business != '3':
                    logger.info('get_all_destiny | CASO 2: business={}, buscando en BD',
                            repr(business), internal=internal, external=external)
                    
                    business_id = session.execute(
                        select(Business.id_business)
                        .where(Business.id_business == business)
                    ).scalar_one_or_none()

                    logger.info('get_all_destiny | business_id encontrado: {}',
                            repr(business_id), internal=internal, external=external)

                    if not business_id:
                        raise CustomAPIException("La empresa no existe", 404)

                    stmt = stmt.where(DestinyIntern.business_id == business_id)

                # Caso 3: business == '3' → sin filtro
                else:
                    logger.info('get_all_destiny | CASO 3: business=3 (Telearseg), sin filtro',
                            internal=internal, external=external)

                # Imprimir query final
                try:
                    compiled = stmt.compile(
                        dialect=postgresql.dialect(),
                        compile_kwargs={"literal_binds": True}
                    )
                    logger.info('get_all_destiny | QUERY: {}', str(compiled),
                            internal=internal, external=external)
                except Exception as qe:
                    compiled = stmt.compile(dialect=postgresql.dialect())
                    logger.info('get_all_destiny | QUERY: {} | PARAMS: {}',
                            str(compiled), compiled.params,
                            internal=internal, external=external)

                result = session.execute(stmt)
                destiny = [
                    {
                        "id_destiny": c.id_destiny,
                        "name": c.name,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at,
                        "business_id": c.business_id
                    }
                    for c in result.scalars().all()
                ]

                logger.info('get_all_destiny | registros retornados: {}',
                        len(destiny), internal=internal, external=external)

                return destiny

            except Exception as exception:
                logger.error('get_all_destiny | Error: {}', str(exception), 
                            internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def get_sector_by_id(self, id_sector, internal, external):
        with self.db.session_factory() as session:
            try:
                sector = session.execute(
                    select(Sector)
                    .where(Sector.id_sector == id_sector)
                ).scalar_one_or_none()

                sector_found = {
                    "id_sector": sector.id_sector,
                    "name": sector.name,
                    "created_at": sector.created_at,
                    "updated_at": sector.updated_at
                }

                return sector_found

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_categories_by_name(self, names_categories, internal, external):
        with self.db.session_factory() as session:
            try:
                stmt = select(Category).where(
                    Category.name_category.in_(names_categories),
                    GroupBusiness.is_active == True
                )

                rows_categories = session.execute(stmt).scalars().all()

                categories = [
                    {
                        "id_category": c.id_category,
                        "name_category": c.name_category,
                        "code": c.code,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    }
                    for c in rows_categories
                ]

                return categories

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_group_business_by_id_business(self, id_business, internal, external):
        with self.db.session_factory() as session:
            try:
                stmt = select(GroupBusiness)

                business_exist = session.get(Business, id_business)

                if not business_exist:
                    raise CustomAPIException("Empresa no existe", 404)
                

                if business_exist.name != "Telearseg":
                    stmt = stmt.where(
                        GroupBusiness.business_id == id_business,
                        GroupBusiness.is_active == True
                    )

                group_business = session.execute(stmt).scalars().all()

                groups_found = [
                    {
                        "id_group_business": gb.id_group_business,
                        "business_id": gb.business_id,
                        "sector_id": gb.sector_id,
                        "name": gb.name,
                        "created_at": gb.created_at,
                        "updated_at": gb.updated_at
                    }
                    for gb in group_business
                ]

                return groups_found

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_sector_by_business(self, id_business, internal, external):
        with self.db.session_factory() as session:
            try:
                business_exist = session.get(Business, id_business)

                if not business_exist:
                    raise CustomAPIException("Empresa no existe", 404)

                query = (
                    session.query(
                        Sector.id_sector,
                        Sector.name,
                        Sector.created_at,
                        Sector.updated_at
                    )
                    .join(GroupBusiness, Sector.id_sector == GroupBusiness.sector_id)
                    .join(Business, Business.id_business == GroupBusiness.business_id)
                )

                if business_exist.name != "Telearseg":
                    query = query.filter(Business.id_business == id_business)

                query = query.group_by(Sector.id_sector)

                result = query.all()

                sectors_found = [
                    {
                        "id_sector": sector.id_sector,
                        "name": sector.name,
                        "created_at": sector.created_at,
                        "updated_at": sector.updated_at
                    }
                    for sector in result
                ]

                return sectors_found

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

            
    def get_all_logbook_entry(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                stmt = (
                    select(
                        LogbookEntry,
                        GroupBusiness.name.label("group_name"),
                        Sector.id_sector.label("id_sector"),
                        Sector.name.label("name_sector"),
                        Category.name_category,
                        func.coalesce(
                            func.array_agg(LogbookImages.image_path)
                                .filter(LogbookImages.image_path.isnot(None)),
                            []
                        ).label("images")
                    )
                    .join(
                        GroupBusiness,
                        GroupBusiness.id_group_business == LogbookEntry.group_business_id
                    )
                    .join(
                        Sector,
                        Sector.id_sector == GroupBusiness.sector_id
                    )
                    .join(
                        Category,
                        Category.id_category == LogbookEntry.category_id
                    )
                    .outerjoin(
                        LogbookImages,
                        LogbookImages.logbook_id_entry == LogbookEntry.id_logbook_entry
                    )
                )

                stmt = stmt.group_by(
                    LogbookEntry.id_logbook_entry,
                    GroupBusiness.name,
                    Sector.id_sector,
                    Sector.name,
                    Category.id_category
                )

                filters = []

                last_30_days = datetime.now() - timedelta(days=30)

                if not filtersBase.get("start_date") and not filtersBase.get("end_date"):
                    filters.append(LogbookEntry.created_at >= last_30_days)

                if filtersBase.get("category_ids"):
                    filters.append(Category.id_category.in_(filtersBase.get("category_ids")))

                if filtersBase.get("sector_id"):
                    filters.append(Sector.id_sector.in_(filtersBase.get("sector_id")))

                if filtersBase.get("user"):
                    filters.append(LogbookEntry.created_by == filtersBase.get("user"))

                if filtersBase.get("groups_business_id"):
                    filters.append(LogbookEntry.group_business_id.in_(filtersBase.get("groups_business_id")))

                if filtersBase.get("start_date"):
                    filters.append(LogbookEntry.created_at >= filtersBase.get("start_date"))

                if filtersBase.get("end_date"):
                    filters.append(LogbookEntry.created_at <= filtersBase.get("end_date"))

                if filtersBase.get("workday"):
                    filters.append(LogbookEntry.workday.in_(filtersBase.get("workday")))

                if filtersBase.get("id_business"):
                    filters.append(GroupBusiness.business_id == filtersBase.get("id_business"))

                if filtersBase.get("notCategory"):
                    filters.append(Category.code != filtersBase.get("notCategory"))

                if filters:
                    stmt = stmt.where(and_(*filters))

                result = session.execute(stmt).all()
                return result

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            

    def get_all_logbook_out(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                stmt = (
                    select(
                        LogbookOut,
                        GroupBusiness.name.label("group_name"),
                        Sector.id_sector.label("id_sector"),
                        Sector.name.label("name_sector"),
                        Category.name_category,
                        func.coalesce(
                            func.array_agg(LogbookImages.image_path)
                                .filter(LogbookImages.image_path.isnot(None)),
                            []
                        ).label("images")
                    )
                    .join(
                        GroupBusiness,
                        GroupBusiness.id_group_business == LogbookOut.group_business_id
                    )
                    .join(
                        Sector,
                        Sector.id_sector == GroupBusiness.sector_id
                    )
                    .join(
                        Category,
                        Category.id_category == LogbookOut.category_id
                    )
                    .outerjoin(
                        LogbookImages,
                        LogbookImages.logbook_id_out == LogbookOut.id_logbook_out
                    )
                )

                stmt = stmt.group_by(
                    LogbookOut.id_logbook_out,
                    GroupBusiness.name,
                    Sector.id_sector,
                    Sector.name,
                    Category.id_category
                )

                filters = []

                last_30_days = datetime.now() - timedelta(days=30)

                if not filtersBase.get("start_date") and not filtersBase.get("end_date"):
                    filters.append(LogbookOut.created_at >= last_30_days)

                if filtersBase.get("category_ids"):
                    filters.append(Category.id_category.in_(filtersBase.get("category_ids")))

                if filtersBase.get("sector_id"):
                    filters.append(Sector.id_sector.in_(filtersBase.get("sector_id")))

                if filtersBase.get("user"):
                    filters.append(LogbookOut.created_by == filtersBase.get("user"))

                if filtersBase.get("groups_business_id"):
                    filters.append(LogbookOut.group_business_id.in_(filtersBase.get("groups_business_id")))

                if filtersBase.get("start_date"):
                    filters.append(LogbookOut.created_at >= filtersBase.get("start_date"))

                if filtersBase.get("end_date"):
                    filters.append(LogbookOut.created_at <= filtersBase.get("end_date"))

                if filtersBase.get("workday"):
                    filters.append(LogbookOut.workday.in_(filtersBase.get("workday")))

                if filtersBase.get("id_business"):
                    filters.append(GroupBusiness.business_id == filtersBase.get("id_business"))

                if filtersBase.get("notCategory"):
                    filters.append(Category.code != filtersBase.get("notCategory"))

                if filters:
                    stmt = stmt.where(and_(*filters))

                result = session.execute(stmt).all()
                return result

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_logbook_resume(self, internal, external, model: LogbookOut | LogbookEntry, filtersBase=None):
        with self.db.session_factory() as session:
            start, end = get_date_range(filtersBase.get('start_date'), filtersBase.get('end_date'))

            try:
                query = (
                    session.query(
                        GroupBusiness.id_group_business,
                        GroupBusiness.name.label("grupo_negocio"),
                        Category.id_category,
                        Category.name_category,
                        func.sum(model.quantity).label("cantidad"),
                        UnityWeight.name.label("unidad"),
                        Sector.id_sector,
                        Sector.name.label("sector")
                    )
                    .join(Category, Category.id_category == model.category_id)
                    .join(UnityWeight, UnityWeight.id_unity == model.unity_id)
                    .join(GroupBusiness, GroupBusiness.id_group_business == model.group_business_id)
                    .join(Sector, Sector.id_sector == GroupBusiness.sector_id)
                    .filter(model.created_at >= start)
                    .filter(model.created_at < end)
                    .group_by(
                        GroupBusiness.id_group_business,
                        GroupBusiness.name,
                        Category.id_category,
                        Category.name_category,
                        UnityWeight.name,
                        Sector.id_sector,
                    )
                    .order_by(GroupBusiness.name)
                )

                filters = []

                if filtersBase.get('sector_id'):
                    filters.append(Sector.id_sector.in_(filtersBase.get('sector_id')))

                if filtersBase.get("groups_business_id"):
                    filters.append(model.group_business_id.in_(filtersBase.get("groups_business_id")))

                if filters:
                    query = query.where(and_(*filters))

                # print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))


                result = session.execute(query).all()

                return result
            
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def get_busnisses_by_id (self, internal, external) -> List[Business]:
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(Business)
                )
                businesses = [
                    {
                        "id_business": b.id_business,
                        "name_business": b.name_business,
                        "code": b.code,
                        "created_at": b.created_at,
                        "updated_at": b.updated_at
                    }
                    for b in result.scalars().all()
                ]
                return businesses
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            
    def post_report_generated(self, datos, internal, external) -> None:
        with self.db.session_factory() as session:
            try:
                business_exists = session.execute(
                    select(
                        exists().where(
                            Business.id_business == datos["business_id"]
                        )
                    )
                ).scalar()

                if not business_exists:
                    raise CustomAPIException(
                        message="No existe la empresa",
                        status_code=404
                    )
                
                new_report = ReportGenerated(
                    business_id=datos["business_id"],
                    type_report=datos["type_report"],
                    status=datos["status"],
                    shipping_error=datos["shipping_error"],
                    created_at=datos["created_at"],
                    deadline=datos["deadline"],
                    shipping_date=datos["shipping_date"],
                    created_by=datos["created_by"],
                    start_date=datos["start_date"],
                )

                session.add(new_report)
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()

    def save_image(self, file):
        folder = "/var/www/uploads/logbooks"
        ALLOWED_EXTENSIONS = {"webp"}
        MAX_FILENAME_LEN = 255
        MAX_BASENAME_LEN = 50

        if not file or file.filename == "":
            raise ValueError("Archivo inválido")

        if not os.path.exists(folder):
            raise CustomAPIException(f"La carpeta root de imágenes no existe {getpass.getuser()} - {os.getuid()} - {os.geteuid()}", 404)
        

        if not os.access(folder, os.W_OK):
            raise CustomAPIException(f"No hay permisos de escritura en la carpeta de imágenes {getpass.getuser()} - {os.getuid()} - {os.geteuid()}", 400)
        
        # ext = file.filename.rsplit(".", 1)[-1].lower()

        # if ext not in ALLOWED_EXTENSIONS:
        #     raise ValueError("Formato no permitido. Solo se acepta WEBP.")

        original_name = secure_filename(file.filename)
        base_name = os.path.splitext(original_name)[0][:MAX_BASENAME_LEN]

        filename = f"{uuid4()}_{base_name}.webp"

        if len(filename.encode("utf-8")) > MAX_FILENAME_LEN:
            filename = f"{uuid4().hex}.webp"

        path = os.path.join(folder, filename)
        file.save(path)

        return {
            "url": f"/uploads/logbooks/{filename}"
        }
    
    def apply_filters(self, stmt, model: LogbookEntry | LogbookOut, filtersBase):
        filters = []
        last_30_days = datetime.now() - timedelta(days=30)

        if not filtersBase.get("start_date") and not filtersBase.get("end_date"):
            filters.append(model.created_at >= last_30_days)

        if filtersBase.get("category_ids"):
            filters.append(model.category_id.in_(filtersBase["category_ids"]))

        if filtersBase.get("user") and filtersBase.get("user") != 'cod_monitoreo' : #TEMPORAL
            filters.append(model.created_by == filtersBase["user"])

        if filtersBase.get("start_date"):
            filters.append(model.created_at >= filtersBase["start_date"])

        if filtersBase.get("end_date"):
            filters.append(model.created_at <= filtersBase["end_date"])

        if filtersBase.get("workday"):
            filters.append(model.workday.in_(filtersBase["workday"]))

        if filtersBase.get("sector_id"):
            filters.append(Sector.id_sector.in_(filtersBase.get("sector_id")))

        if filtersBase.get("groups_business_id"):
            filters.append(model.group_business_id.in_(filtersBase.get("groups_business_id")))

        if filtersBase.get("id_business"):
            filters.append(GroupBusiness.business_id == filtersBase.get("id_business"))

        if filtersBase.get("notCategory"):
            filters.append(Category.code != filtersBase.get("notCategory"))

        if filters:
            stmt = stmt.where(and_(*filters))

        return stmt
    

    def apply_filters_union_all(self, model: LogbookEntry | LogbookOut, filtersBase):
        filters = []
        last_30_days = datetime.now() - timedelta(days=30)

        if not filtersBase.get("start_date") and not filtersBase.get("end_date"):
            filters.append(model.created_at >= last_30_days)

        if filtersBase.get("category_ids"):
            filters.append(model.category_id.in_(filtersBase["category_ids"]))

        if filtersBase.get("user") and filtersBase.get("user") != 'cod_monitoreo' : #TEMPORAL
            filters.append(model.created_by == filtersBase["user"])

        if filtersBase.get("start_date"):
            filters.append(model.created_at >= filtersBase["start_date"])

        if filtersBase.get("end_date"):
            filters.append(model.created_at <= filtersBase["end_date"])

        if filtersBase.get("workday"):
            filters.append(model.workday.in_(filtersBase["workday"]))

        if filtersBase.get("sector_id"):
            filters.append(Sector.id_sector.in_(filtersBase.get("sector_id")))

        if filtersBase.get("groups_business_id"):
            filters.append(model.group_business_id.in_(filtersBase.get("groups_business_id")))

        if filtersBase.get("id_business"):
            filters.append(GroupBusiness.business_id == filtersBase.get("id_business"))

        if filtersBase.get("notCategory"):
            filters.append(Category.code != filtersBase.get("notCategory"))

        column_search = SEARCH_COLUMNS_OUT if model is LogbookOut else SEARCH_COLUMNS_ENTRY
        apply_search(filters, filtersBase.get("search"), column_search)

        return filters if filters else [true()]

        return stmt

    def get_logbook_out(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                images_out_subq = (
                    select(
                        LogbookImages.logbook_id_out.label("logbook_id"),
                        func.array_agg(LogbookImages.image_path).label("images")
                    )
                    .where(LogbookImages.image_path.isnot(None))
                    .group_by(LogbookImages.logbook_id_out)
                    .subquery()
                )

                stmt_out = (
                    select(
                        LogbookOut,
                        GroupBusiness.name.label("group_name"),
                        Sector.id_sector.label("id_sector"),
                        Sector.name.label("name_sector"),
                        Category.name_category,
                        func.coalesce(images_out_subq.c.images, []).label("images_out")
                    )
                    .join(GroupBusiness, GroupBusiness.id_group_business == LogbookOut.group_business_id)
                    .join(Sector, Sector.id_sector == GroupBusiness.sector_id)
                    .join(Category, Category.id_category == LogbookOut.category_id)
                    .outerjoin(LogbookEntry, LogbookEntry.logbook_out_id == LogbookOut.id_logbook_out)
                    .outerjoin(
                        images_out_subq,
                        images_out_subq.c.logbook_id == LogbookOut.id_logbook_out
                    )
                    .where(LogbookEntry.id_logbook_entry.is_(None))
                )

                stmt_out = self.apply_filters(stmt_out, LogbookOut, filtersBase)

                rows_out = session.execute(stmt_out).all()

                return rows_out

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al buscar en la base de datos", 500)

            finally:
                session.close()


    def request_idempotency(self, session, data: RequestIdempotency, internal, external):
        try:
            
            uuid_request_exist = session.execute(
                select(
                    exists().where(
                        RequestIdempotency.uuid == data.uuid
                    )
                )
            ).scalar()

            if uuid_request_exist:
                raise CustomAPIException(
                    message="Duplicación de registro, el external transaction ya existe",
                    status_code=409
                )

            session.add(data)
            # session.commit()

        except Exception as exception:
            logger.error('Error: {}', str(exception), internal=internal, external=external)
            if isinstance(exception, CustomAPIException):
                raise exception
            
            raise CustomAPIException("Error al buscar en la base de datos", 500)


    def get_logbook_entry(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                CategoryOut = aliased(Category)
                images_entry_subq = (
                    select(
                        LogbookImages.logbook_id_entry.label("logbook_id"),
                        func.array_agg(LogbookImages.image_path).label("images")
                    )
                    .where(LogbookImages.image_path.isnot(None))
                    .group_by(LogbookImages.logbook_id_entry)
                    .subquery()
                )

                images_out_subq = (
                    select(
                        LogbookImages.logbook_id_out.label("logbook_id"),
                        func.array_agg(LogbookImages.image_path).label("images")
                    )
                    .where(LogbookImages.image_path.isnot(None))
                    .group_by(LogbookImages.logbook_id_out)
                    .subquery()
                )

                stmt_entry = (
                    select(
                        LogbookEntry,
                        LogbookOut,
                        GroupBusiness.name.label("group_name"),
                        Sector.id_sector.label("id_sector"),
                        Sector.name.label("name_sector"),
                        Category.name_category.label("name_category_entry"),
                        CategoryOut.name_category.label("name_category_out"),
                        func.coalesce(images_entry_subq.c.images, []).label("images_entry"),
                        func.coalesce(images_out_subq.c.images, []).label("images_out")

                        # func.coalesce(
                        #     images_entry_subq.c.images,
                        #     cast([], ARRAY(String))  # 👈 ARRAY[]::varchar[] en lugar de []
                        # ).label("images_entry"),
                        # func.coalesce(
                        #     images_out_subq.c.images,
                        #     cast([], ARRAY(String))  # 👈
                        # ).label("images_out")
                    )
                    .join(GroupBusiness, GroupBusiness.id_group_business == LogbookEntry.group_business_id)
                    .join(Sector, Sector.id_sector == GroupBusiness.sector_id)
                    .join(Category, Category.id_category == LogbookEntry.category_id)
                    .outerjoin(LogbookOut, LogbookOut.id_logbook_out == LogbookEntry.logbook_out_id)
                    .outerjoin(CategoryOut, CategoryOut.id_category == LogbookOut.category_id)
                    .outerjoin(
                        images_entry_subq,
                        images_entry_subq.c.logbook_id == LogbookEntry.id_logbook_entry
                    )
                    .outerjoin(
                        images_out_subq,
                        images_out_subq.c.logbook_id == LogbookOut.id_logbook_out
                    )
                )

                stmt_entry = self.apply_filters(stmt_entry, LogbookEntry, filtersBase)
                rows_entry = session.execute(stmt_entry).all()

                return rows_entry

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al buscar en la base de datos", 500)

            finally:
                session.close()

    def print_query(self, stmt):
        try:
            compiled = stmt.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True}
            )
            print("\n" + "=" * 80)
            print(str(compiled))
            print("=" * 80 + "\n")
        except Exception:
            compiled = stmt.compile(dialect=postgresql.dialect())
            params = compiled.params
            query_str = str(compiled)
            # Sustituye manualmente los parámetros
            for key, value in params.items():
                if isinstance(value, str):
                    query_str = query_str.replace(f"%({key})s", f"'{value}'")
                elif value is None:
                    query_str = query_str.replace(f"%({key})s", "NULL")
                else:
                    query_str = query_str.replace(f"%({key})s", str(value))
            print("\n" + "=" * 80)
            print(query_str)
            print("=" * 80 + "\n")


    def get_all_logbooks_paginated(self, filtersBase, pagination, internal, external):
        with self.db.session_factory() as session:
            try:
                # ── Subquery de imágenes OUT ──────────────────────────────────
                images_out_subq = (
                    select(
                        LogbookImages.logbook_id_out.label("logbook_id"),
                        func.array_agg(LogbookImages.image_path)
                            .filter(LogbookImages.image_path.isnot(None))
                            .label("images")
                    )
                    .group_by(LogbookImages.logbook_id_out)
                    .subquery()
                )

                # ── Subquery de imágenes ENTRY ────────────────────────────────
                images_entry_subq = (
                    select(
                        LogbookImages.logbook_id_entry.label("logbook_id"),
                        func.array_agg(LogbookImages.image_path)
                            .filter(LogbookImages.image_path.isnot(None))
                            .label("images")
                    )
                    .group_by(LogbookImages.logbook_id_entry)
                    .subquery()
                )

                # ── Rama OUT ──────────────────────────────────────────────────
                out_filters = self.apply_filters_union_all(LogbookOut, filtersBase)

                stmt_out = (
                    select(
                        literal("out").label("record_type"),
                        LogbookOut.id_logbook_out.label("record_id"),
                        cast(None, Integer).label("logbook_out_id"),   # entry relacionado: N/A
                        LogbookOut.unity_id,
                        LogbookOut.category_id,
                        LogbookOut.group_business_id,
                        GroupBusiness.name.label("group_name"),
                        Sector.id_sector,
                        Sector.name.label("name_sector"),
                        Category.name_category,
                        LogbookOut.name_user,
                        LogbookOut.shipping_guide,
                        LogbookOut.quantity,
                        LogbookOut.weight,
                        LogbookOut.truck_license,
                        LogbookOut.name_driver,
                        LogbookOut.authorized_by,
                        LogbookOut.observations,
                        LogbookOut.workday,
                        LogbookOut.lat,
                        LogbookOut.long,
                        LogbookOut.destiny.label("destiny"),           # campo unificado
                        LogbookOut.person_withdraws,
                        cast(None, Text).label("description"),         # exclusivo entry
                        cast(None, Text).label("provider"),
                        cast(None, Text).label("status"),
                        func.coalesce(images_out_subq.c.images, cast([], ARRAY(Text))).label("images"),
                        LogbookOut.created_at,
                        LogbookOut.updated_at,
                        LogbookOut.created_by,
                        LogbookOut.updated_by,

                        cast(None, Integer).label("out_record_id"),
                        cast(None, Integer).label("out_unity_id"),
                        cast(None, Integer).label("out_category_id"),
                        cast(None, Integer).label("out_group_business_id"),
                        cast(None, Text).label("out_name_user"),
                        cast(None, Text).label("out_shipping_guide"),
                        cast(None, Integer).label("out_quantity"),
                        cast(None, Integer).label("out_weight"),
                        cast(None, Text).label("out_truck_license"),
                        cast(None, Text).label("out_name_driver"),
                        cast(None, Text).label("out_authorized_by"),
                        cast(None, Text).label("out_observations"),
                        cast(None, Text).label("out_workday"),
                        cast(None, Text).label("out_lat"),
                        cast(None, Text).label("out_long"),
                        cast(None, Text).label("out_destiny"),
                        cast(None, Text).label("out_person_withdraws"),
                        cast(None, DateTime).label("out_created_at"),
                        cast(None, DateTime).label("out_updated_at"),
                        cast(None, Text).label("out_created_by"),
                        cast(None, Text).label("out_updated_by"),
                        cast(None, Text).label("out_name_category"),
                        cast(None, Text).label("out_group_name"),
                        cast([], ARRAY(Text)).label("out_images"),
                    )
                    .join(GroupBusiness, GroupBusiness.id_group_business == LogbookOut.group_business_id)
                    .join(Sector, Sector.id_sector == GroupBusiness.sector_id)
                    .join(Category, Category.id_category == LogbookOut.category_id)
                    .outerjoin(images_out_subq, images_out_subq.c.logbook_id == LogbookOut.id_logbook_out)
                    # Solo out sin entry asociado
                    .outerjoin(LogbookEntry, LogbookEntry.logbook_out_id == LogbookOut.id_logbook_out)
                    .where(LogbookEntry.id_logbook_entry.is_(None))
                    .where(and_(*out_filters))
                )

                # ── Rama ENTRY ────────────────────────────────────────────────
                entry_filters = self.apply_filters_union_all(LogbookEntry, filtersBase)

                CategoryOut = aliased(Category)
                GroupBusinessOut = aliased(GroupBusiness)
                images_out_related_subq = (
                    select(
                        LogbookImages.logbook_id_out.label("logbook_id"),
                        func.array_agg(LogbookImages.image_path)
                            .filter(LogbookImages.image_path.isnot(None))
                            .label("images")
                    )
                    .group_by(LogbookImages.logbook_id_out)
                    .subquery()
                )

                LogbookOutRelated = aliased(LogbookOut)

                stmt_entry = (
                    select(
                        literal("entry").label("record_type"),
                        LogbookEntry.id_logbook_entry.label("record_id"),
                        LogbookEntry.logbook_out_id,               # referencia al out relacionado
                        LogbookEntry.unity_id,
                        LogbookEntry.category_id,
                        LogbookEntry.group_business_id,
                        GroupBusiness.name.label("group_name"),
                        Sector.id_sector,
                        Sector.name.label("name_sector"),
                        Category.name_category,
                        LogbookEntry.name_user,
                        LogbookEntry.shipping_guide,
                        LogbookEntry.quantity,
                        LogbookEntry.weight,
                        LogbookEntry.truck_license,
                        LogbookEntry.name_driver,
                        LogbookEntry.authorized_by,
                        LogbookEntry.observations,
                        LogbookEntry.workday,
                        LogbookEntry.lat,
                        LogbookEntry.long,
                        LogbookEntry.destiny_intern.label("destiny"),  # campo unificado
                        cast(None, Text).label("person_withdraws"),    # exclusivo out
                        LogbookEntry.description,
                        LogbookEntry.provider,
                        LogbookEntry.status,
                        func.coalesce(images_entry_subq.c.images, cast([], ARRAY(Text))).label("images"),
                        LogbookEntry.created_at,
                        LogbookEntry.updated_at,
                        LogbookEntry.created_by,
                        LogbookEntry.updated_by,

                        # ── Datos del out relacionado ──────────────────────────
                        LogbookOutRelated.id_logbook_out.label("out_record_id"),
                        LogbookOutRelated.unity_id.label("out_unity_id"),
                        LogbookOutRelated.category_id.label("out_category_id"),
                        LogbookOutRelated.group_business_id.label("out_group_business_id"),
                        LogbookOutRelated.name_user.label("out_name_user"),
                        LogbookOutRelated.shipping_guide.label("out_shipping_guide"),
                        LogbookOutRelated.quantity.label("out_quantity"),
                        LogbookOutRelated.weight.label("out_weight"),
                        LogbookOutRelated.truck_license.label("out_truck_license"),
                        LogbookOutRelated.name_driver.label("out_name_driver"),
                        LogbookOutRelated.authorized_by.label("out_authorized_by"),
                        LogbookOutRelated.observations.label("out_observations"),
                        LogbookOutRelated.workday.label("out_workday"),
                        LogbookOutRelated.lat.label("out_lat"),
                        LogbookOutRelated.long.label("out_long"),
                        LogbookOutRelated.destiny.label("out_destiny"),
                        LogbookOutRelated.person_withdraws.label("out_person_withdraws"),
                        LogbookOutRelated.created_at.label("out_created_at"),
                        LogbookOutRelated.updated_at.label("out_updated_at"),
                        LogbookOutRelated.created_by.label("out_created_by"),
                        LogbookOutRelated.updated_by.label("out_updated_by"),
                        CategoryOut.name_category.label("out_name_category"),
                        GroupBusinessOut.name.label("out_group_name"),
                        func.coalesce(images_out_related_subq.c.images, cast([], ARRAY(Text))).label("out_images"),
                    )
                    .join(GroupBusiness, GroupBusiness.id_group_business == LogbookEntry.group_business_id)
                    .join(Sector, Sector.id_sector == GroupBusiness.sector_id)
                    .join(Category, Category.id_category == LogbookEntry.category_id)
                    .outerjoin(images_entry_subq, images_entry_subq.c.logbook_id == LogbookEntry.id_logbook_entry)

                    # ── Joins del out relacionado ──────────────────────────────
                    .outerjoin(LogbookOutRelated, LogbookOutRelated.id_logbook_out == LogbookEntry.logbook_out_id)
                    .outerjoin(CategoryOut, CategoryOut.id_category == LogbookOutRelated.category_id)
                    .outerjoin(GroupBusinessOut, GroupBusinessOut.id_group_business == LogbookOutRelated.group_business_id)
                    .outerjoin(images_out_related_subq, images_out_related_subq.c.logbook_id == LogbookOutRelated.id_logbook_out)

                    .where(and_(*entry_filters))
                )

                # ── UNION ALL + orden + paginación ────────────────────────────
                union_subq = union_all(stmt_out, stmt_entry).subquery()


                total_stmt = select(func.count()).select_from(union_subq)
                total = session.execute(total_stmt).scalar()

                final_stmt = (
                    select(union_subq)
                    .order_by(union_subq.c.created_at.desc())
                    .offset(pagination.offset)
                    .limit(pagination.page_size)
                )
                
                rows = session.execute(final_stmt).mappings().all()

                return rows, total

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                raise CustomAPIException("Error al buscar en la base de datos", 500)
            finally:
                session.close()