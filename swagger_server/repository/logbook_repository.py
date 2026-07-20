

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from unittest import result
from flask import json
from loguru import logger
from sqlalchemy import ARRAY, Boolean, DateTime, Integer, String, Text, and_, case, cast, exists, func, insert, literal, or_, select, text, true, union_all
from sqlalchemy.orm import aliased
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.assign_order_data import AssignOrderData
from swagger_server.models.db.authorized import Authorized
from swagger_server.models.db.blacklist_drivers import BlacklistDrivers
from swagger_server.models.db.business import Business
from swagger_server.models.db.business import Business
from swagger_server.models.db.destiny_intern import DestinyIntern
from swagger_server.models.db.employee_intern import EmployeeIntern
from swagger_server.models.db.group_business import GroupBusiness
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.category import Category
from swagger_server.models.db.logbook_images import LogbookImages
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.db.order_receipts_image import OrderReceiptsImages
from swagger_server.models.db.purchase_order import PurchaseOrder
from swagger_server.models.db.purchase_order_destinations import PurchaseOrderDestinations
from swagger_server.models.db.purchase_order_receipts import PurchaseOrderReceipts
from swagger_server.models.db.reason_restriction import ReasonRestriction
from swagger_server.models.db.status_purchase_order import StatusPurchaseOrder
from swagger_server.models.db.report_generated import ReportGenerated
from swagger_server.models.db.request_idempotency import RequestIdempotency
from swagger_server.models.db.sector import Sector
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.models.purchase_order_data import PurchaseOrderData
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


    def post_logbook_entry(self, logbook_entry_body: LogbookEntry, order_id, images, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/post/logbook-entry"
                )
                
                self.request_idempotency(session, data_request, internal, external)
                
                if logbook_entry_body.unity_id is not None and logbook_entry_body.unity_id != 0:
                    unity_weight_exists = session.execute(
                        select(
                            exists().where(
                                UnityWeight.id_unity == logbook_entry_body.unity_id
                            )
                        )
                    ).scalar()

                    if not unity_weight_exists:
                        raise CustomAPIException(
                            message="No existe la unidad de peso",
                            status_code=404
                        )

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

                if not category:
                    raise CustomAPIException(
                        message="No existe la categoría",
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
                
                if category.name_category == "Balanceado" or category.name_category == "Combustibles":
                    body_purchase = {
                        "purchase_order_id": order_id,
                        "logbook_entry_id": logbook_entry_id,
                        "quantity": logbook_entry_body.quantity,
                        "user": logbook_entry_body.created_by
                    }

                    self.post_order_receipts(session, body_purchase, internal, external)

                #Guardar imágenes (máx 10)
                # for file in images[:10]:
                #     result = self.save_image(file)
                #     saved_files.append(result["url"])

                #     image = LogbookImages(
                #         logbook_id_entry=logbook_entry_id,
                #         image_path=result["url"]
                #     )

                #     session.add(image)

                session.commit()

                # logbook_entry_dict = logbook_entry_body.to_dict()
                # logbook_entry_dict["name_category"] = category.name_category
                # logbook_entry_dict["group_name"] = group_business_exists.name

                # self.redis_client.client.publish(
                #     "logbook_channel",
                #     json.dumps({
                #         "type": "logbook_saved",
                #         "logbook": logbook_entry_dict
                #     })
                # )

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

                if logbook_out_body.unity_id is not None:
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

                # logbook_out_dict = logbook_out_body.to_dict()
                # logbook_out_dict["name_category"] = category.name_category
                # logbook_out_dict["group_name"] = group_business_exists.name

                # self.redis_client.client.publish(
                #     "logbook_channel",
                #     json.dumps({
                #         "type": "logbook_saved",
                #         "logbook": logbook_out_dict
                #     })
                # )


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

    def get_all_categories(self, filters, internal, external):
        with self.db.session_factory() as session:
            try:
                if filters.get("codes"):
                    result = session.execute(
                        select(Category).where(Category.code.in_(filters["codes"]))
                    )
                else:
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
                # logger.info('get_all_destiny | business recibido: {} | type: {}', 
                #         repr(business), type(business).__name__, 
                #         internal=internal, external=external)

                stmt = select(DestinyIntern)

                # Caso 1: no viene business → default = 1
                if not business:
                    # logger.info('get_all_destiny | CASO 1: business vacío, filtrando por business_id=1',
                    #         internal=internal, external=external)
                    stmt = stmt.where(DestinyIntern.business_id == 1)

                # Caso 2: viene business distinto de Telearseg → filtrar
                elif business != '3':
                    # logger.info('get_all_destiny | CASO 2: business={}, buscando en BD',
                    #         repr(business), internal=internal, external=external)
                    
                    business_id = session.execute(
                        select(Business.id_business)
                        .where(Business.id_business == business)
                    ).scalar_one_or_none()

                    # logger.info('get_all_destiny | business_id encontrado: {}',
                    #         repr(business_id), internal=internal, external=external)

                    if not business_id:
                        raise CustomAPIException("La empresa no existe", 404)

                    stmt = stmt.where(DestinyIntern.business_id == business_id)

                # Caso 3: business == '3' → sin filtro
                # else:
                #     logger.info('get_all_destiny | CASO 3: business=3 (Telearseg), sin filtro',
                #             internal=internal, external=external)

                # Imprimir query final
                # try:
                #     compiled = stmt.compile(
                #         dialect=postgresql.dialect(),
                #         compile_kwargs={"literal_binds": True}
                #     )
                #     logger.info('get_all_destiny | QUERY: {}', str(compiled),
                #             internal=internal, external=external)
                # except Exception as qe:
                #     compiled = stmt.compile(dialect=postgresql.dialect())
                #     logger.info('get_all_destiny | QUERY: {} | PARAMS: {}',
                #             str(compiled), compiled.params,
                #             internal=internal, external=external)

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
            

    def get_group_business_by_sector(self, id_sector, internal, external):
        with self.db.session_factory() as session:
            try:

                sector_exist = session.get(Sector, id_sector)

                if not sector_exist:
                    raise CustomAPIException("Sector no existe", 404)
                

                stmt = select(GroupBusiness).where(
                    GroupBusiness.sector_id == id_sector,
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

    def save_image(self, file, name_folder="logbooks"):
        folder = f"/var/www/uploads/{name_folder}"
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
            "url": f"/uploads/{name_folder}/{filename}"
        }
    

    def delete_image(self, image_path):
        if not image_path:
            return

        full_path = os.path.join("/var/www", image_path.lstrip("/"))

        if not os.path.exists(full_path):
            raise CustomAPIException("El archivo no existe", 404)

        if not os.access(full_path, os.W_OK):
            raise CustomAPIException("No hay permisos para eliminar el archivo", 400)

        try:
            os.remove(full_path)
        except Exception as e:
            raise CustomAPIException(f"Error al eliminar la imagen: {str(e)}", 500)

    
    def apply_filters(self, stmt, model: LogbookEntry | LogbookOut, filtersBase):
        filters = []
        last_30_days = datetime.now() - timedelta(days=30)
        id_logbook = filtersBase.get("id_logbook")

        if not filtersBase.get("start_date") and not filtersBase.get("end_date"):
            filters.append(model.created_at >= last_30_days)

        if filtersBase.get("category_ids"):
            filters.append(model.category_id.in_(filtersBase["category_ids"]))

        if filtersBase.get("user") and filtersBase.get("user") != 'cod_monitoreo' : #TEMPORAL
            filters.append(model.created_by == filtersBase["user"])

        if id_logbook:
            field = (
                model.id_logbook_entry
                if model is LogbookEntry
                else model.id_logbook_out
            )

            filters.append(field == id_logbook)

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

        if not filtersBase.get("start_date") and not filtersBase.get("end_date") and not filtersBase.get("search"):
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
                        LogbookOut.dni_driver,
                        LogbookOut.is_blacklist,
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
                        cast(None, Text).label("out_dni_driver"),
                        cast(None, Boolean).label("out_is_blacklist"),
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
                        LogbookEntry.dni_driver,
                        LogbookEntry.is_blacklist,
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
                        LogbookOutRelated.dni_driver.label("out_dni_driver"),
                        LogbookOutRelated.is_blacklist.label("out_is_blacklist"),
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

    
    def save_lead(self, data, internal, external):
        with self.db.session_factory() as session:
            try:

                register_exist = text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM public.register_lead
                        WHERE email = :email
                    )
                """)

                # if session.execute(
                #     register_exist,
                #     {"email": data.email}
                # ).scalar():
                #     raise CustomAPIException(
                #         message="El correo ya se encuentra registrado",
                #         status_code=400
                #     )

                query = text("""
                    INSERT INTO public.register_lead
                    (
                        names,
                        phone,
                        email,
                        business,
                        position,
                        interested
                    )
                    VALUES
                    (
                        :names,
                        :phone,
                        :email,
                        :business,
                        :position,
                        :interested
                    )
                    RETURNING *
                """)

                result = session.execute(
                    query,
                    {
                        "names": data.names,
                        "phone": data.phone,
                        "email": data.email,
                        "business": data.business,
                        "position": data.position,
                        "interested": data.interested,
                    }
                )

                created_register = result.mappings().first()

                session.commit()

                return created_register

            except Exception as exception:
                session.rollback()

                logger.error(
                    'Error: {}',
                    str(exception),
                    internal=internal,
                    external=external
                )

                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException(
                    "Error al insertar en la base de datos",
                    500
                )

            finally:
                session.close()


    def get_leads(self, internal, external):
        with self.db.session_factory() as session:
            try:
                query = text("""
                    SELECT * 
                    FROM public.register_lead
                    ORDER BY created_at desc
                """)

                rows = session.execute(query).mappings().all()

                data = [
                    {
                        "id_lead": row["id_lead"],
                        "names": row["names"],
                        "email": row["email"],
                        "business": row["business"],
                        "interested": row["interested"],
                        "position": row["position"],
                        "phone": row["phone"],
                        "created_at": row["created_at"],
                    }
                    for row in rows
                ]

                return data
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def get_blacklist(self, filters, internal, external):
        with self.db.session_factory() as session:
            try:
                stmt = (
                    select(BlacklistDrivers).order_by(BlacklistDrivers.created_at.desc())
                )

                if filters.get("dni"):
                    stmt = stmt.where(BlacklistDrivers.dni == filters.get("dni"))

                rows = session.execute(stmt).scalars().all()

                blacklist = [
                    {
                        "id_blacklist": c.id_blacklist,
                        "dni": c.dni,
                        "full_names": c.full_names,
                        "reason_restriction": c.reason_restriction,
                        "observations": c.observations,
                        "image_path": c.image_path,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at,
                        "created_by": c.created_by,
                        "updated_by": c.updated_by,
                    }
                    for c in rows
                ]
                return blacklist
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def post_blacklist(self, blacklist_body, images, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                dni_blacklist_exist = session.execute(
                    select(BlacklistDrivers).where(
                        BlacklistDrivers.dni == blacklist_body.dni
                    )
                ).scalar_one_or_none()
                
                if dni_blacklist_exist:
                    raise CustomAPIException("Cédula ya registrada", 400)

                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/post/blacklist-driver"
                )

                self.request_idempotency(session, data_request, internal, external)

                image_path = None

                # Guardar una sola imagen en la carpeta blacklist
                if images:
                    result = self.save_image(images[0], "blacklist")
                    saved_files.append(result["url"])
                    image_path = result["url"]

                blacklist_driver = BlacklistDrivers(
                    dni=blacklist_body.dni,
                    business_id=blacklist_body.business_id,
                    full_names=blacklist_body.full_names,
                    reason_restriction=blacklist_body.reason_restriction,
                    observations=blacklist_body.observations,
                    image_path=image_path,
                    created_by=blacklist_body.user,
                    updated_by=blacklist_body.user,
                )

                session.add(blacklist_driver)
                session.commit()

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

    def get_order(self, filters, internal, external):
        with self.db.session_factory() as session:
            try:

                last_destiny_subq = (
                    select(
                        PurchaseOrderDestinations.order_id,
                        PurchaseOrderDestinations.destiny_id
                    )
                    .distinct(PurchaseOrderDestinations.order_id)
                    .order_by(
                        PurchaseOrderDestinations.order_id,
                        PurchaseOrderDestinations.id_purchase_destiny.desc()
                    )
                    .subquery()
                )

                destinations_subq = (
                    select(
                        PurchaseOrderDestinations.order_id.label("order_id"),
                        func.json_agg(
                            func.json_build_object(
                                "id", GroupBusiness.id_group_business,
                                "name", GroupBusiness.name
                            )
                        ).label("destinations")
                    )
                    .join(
                        GroupBusiness,
                        GroupBusiness.id_group_business == PurchaseOrderDestinations.destiny_id
                    )
                    .group_by(PurchaseOrderDestinations.order_id)
                    .subquery()
                )

                logbook_images_subq = (
                    select(
                        LogbookImages.logbook_id_entry.label("logbook_entry_id"),
                        func.array_agg(LogbookImages.image_path)
                            .filter(LogbookImages.image_path.isnot(None))
                            .label("images")
                    )
                    .group_by(LogbookImages.logbook_id_entry)
                    .subquery()
                )
                
                receipts_subq = (
                    select(
                        PurchaseOrderReceipts.purchase_order_id.label("purchase_order_id"),
                        func.json_agg(
                            func.json_build_object(
                                "id_receipts", PurchaseOrderReceipts.id_receipts,
                                "purchase_order_id", PurchaseOrderReceipts.purchase_order_id,
                                "converted_amount", PurchaseOrderReceipts.converted_amount,
                                "created_at", PurchaseOrderReceipts.created_at,
                                "images", func.coalesce(logbook_images_subq.c.images, cast([], ARRAY(Text))),
                                "logbook_entry", case(
                                    (
                                        LogbookEntry.id_logbook_entry.is_not(None),
                                        func.json_build_object(
                                            "id_logbook_entry", LogbookEntry.id_logbook_entry,
                                            "truck_license", LogbookEntry.truck_license,
                                            "driver", LogbookEntry.name_driver,
                                            "shipping_guide", LogbookEntry.shipping_guide,
                                            "user", LogbookEntry.created_by,
                                            "name_user", LogbookEntry.name_user,
                                            "quantity", LogbookEntry.quantity
                                        )
                                    ),
                                    else_=None
                                )

                            )
                        ).label("receipts")
                    )
                    .outerjoin(logbook_images_subq, logbook_images_subq.c.logbook_entry_id == PurchaseOrderReceipts.logbook_entry_id)
                    .outerjoin(LogbookEntry, LogbookEntry.id_logbook_entry == PurchaseOrderReceipts.logbook_entry_id)
                    .group_by(PurchaseOrderReceipts.purchase_order_id)
                    .subquery()
                )

                stmt = (
                    select(
                        PurchaseOrder,
                        StatusPurchaseOrder.name.label("status_name"),
                        destinations_subq.c.destinations,
                        receipts_subq.c.receipts
                    )
                    .outerjoin(
                        receipts_subq,
                        receipts_subq.c.purchase_order_id == PurchaseOrder.id_order
                    )
                    .outerjoin(
                        StatusPurchaseOrder,
                        StatusPurchaseOrder.id_status == PurchaseOrder.status_id
                    )
                    .outerjoin(
                        destinations_subq,
                        destinations_subq.c.order_id == PurchaseOrder.id_order
                    )
                    .outerjoin(
                        last_destiny_subq,
                        last_destiny_subq.c.order_id == PurchaseOrder.id_order
                    )
                    .order_by(PurchaseOrder.created_at.desc())
                )

                if filters.get("rol") == "guardia":
                    stmt = stmt.where(
                        PurchaseOrder.end_date > datetime.now(),
                        PurchaseOrder.status_id.in_([1, 3])
                    )

                    if filters.get("destiny_id"):
                        stmt = stmt.where(
                            or_(
                                PurchaseOrder.flag_all_destinies.is_(True),
                                last_destiny_subq.c.destiny_id.in_(filters["destiny_id"])
                            )
                        )

                elif filters.get("destiny_id"):
                    stmt = stmt.join(
                        PurchaseOrderDestinations,
                        PurchaseOrderDestinations.order_id == PurchaseOrder.id_order
                    ).where(
                        PurchaseOrderDestinations.destiny_id.in_(filters["destiny_id"])
                    )


                if filters.get("status"):
                    status = session.execute(
                        select(StatusPurchaseOrder).where(
                            func.lower(StatusPurchaseOrder.name) ==
                            filters.get("status").lower()
                        )
                    ).scalar_one_or_none()

                    if not status:
                        raise CustomAPIException(
                            message="Estado de busqueda no existe",
                            status_code=404
                        )

                    stmt = stmt.where(PurchaseOrder.status_id == status.id_status)

                if filters.get("without_receipts"):
                    stmt = stmt.where(
                        ~exists(
                            select(1).where(
                                PurchaseOrderReceipts.purchase_order_id == PurchaseOrder.id_order
                            )
                        )
                    )

                rows = session.execute(stmt).all()

                orders = [
                    {
                        "id_order": c.id_order,
                        "status_id": c.status_id,
                        "status_name": status_name,
                        "destinations": destinations,
                        "start_date": c.start_date,
                        "end_date": c.end_date,
                        "number_order": c.number_order,
                        "type_order": c.type_order,
                        "quantity": c.quantity,
                        "remaining_quantity": c.remaining_quantity,
                        "provider": c.provider,
                        "observations": c.observations,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at,
                        "created_by": c.created_by,
                        "updated_by": c.updated_by,
                        "receipts": receipts or None,
                    }
                    for c, status_name, destinations, receipts in rows
                ]

                return orders

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def post_order(self, body: PurchaseOrderData, internal, external) -> None:
        with self.db.session_factory() as session:
            try:
                purchase_order_body = PurchaseOrder(
                    # destiny_id=body.destiny_id,
                    start_date=body.start_date,
                    end_date=body.end_date,
                    number_order=body.number_order,
                    type_order=body.type_order,
                    quantity=body.quantity,
                    provider=body.provider,
                    observations=body.observations,
                    created_by=body.user,
                    updated_by=body.user
                )

                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/post/purchase-order"
                )

                self.request_idempotency(session, data_request, internal, external)

                status = session.execute(
                    select(StatusPurchaseOrder).where(
                        StatusPurchaseOrder.name == "Programado"
                    )
                ).scalar_one_or_none()

                if not status:
                    raise CustomAPIException(
                        message="No existe el estado Programado",
                        status_code=404
                    )

                purchase_order_body.status_id = status.id_status
                session.add(purchase_order_body)
                session.flush()

                destinations = PurchaseOrderDestinations(
                    destiny_id=body.destiny_id,
                    order_id=purchase_order_body.id_order,
                    created_by=body.user,
                )

                session.add(destinations)
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()


    def patch_order(self, id_order: int, body: PurchaseOrderData, internal: str, external: str) -> None:
        with self.db.session_factory() as session:
            try:
                purchase_order_body = PurchaseOrder(
                    start_date=body.start_date,
                    end_date=body.end_date,
                    number_order=body.number_order,
                    type_order=body.type_order,
                    quantity=body.quantity,
                    provider=body.provider,
                    observations=body.observations,
                    updated_by=body.user,
                    updated_at=datetime.now(),
                    flag_all_destinies=body.flag_all_destinies
                )

                purchase_order_exists = session.execute(
                    select(PurchaseOrder)
                    .where(
                        PurchaseOrder.id_order == id_order
                    )
                    .with_for_update()
                ).scalar_one_or_none()

                if not purchase_order_exists:
                    raise CustomAPIException(message="No existe la orden de compra", status_code=404)
                
                if body.status_update:
                    status = session.execute(
                        select(StatusPurchaseOrder).where(
                            StatusPurchaseOrder.name == body.status_update
                        )
                    ).scalar_one_or_none()

                    if not status:
                        raise CustomAPIException(
                            message=f"No existe el estado {body.status_update}",
                            status_code=404
                        )

                    purchase_order_exists.status_id = status.id_status


                # Actualizar los campos de la orden de compra existente
                for key, value in purchase_order_body.to_dict().items():
                    if key != "id_order" and value is not None:
                        setattr(purchase_order_exists, key, value)
                
                if body.destiny_id:
                    destinations = PurchaseOrderDestinations(
                        destiny_id=body.destiny_id,
                        order_id=id_order,
                        created_by=body.user,
                    )
                    session.add(destinations)

                session.add(purchase_order_exists)
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al actualizar en la base de datos", 500)

            finally:
                session.close()


    def get_order_receipts(self, filters, internal, external):
        with self.db.session_factory() as session:
            try:
                receipts_images_subq = (
                    select(
                        LogbookImages.logbook_id_entry.label("logbook_entry_id"),
                        func.array_agg(LogbookImages.image_path)
                            .filter(LogbookImages.image_path.isnot(None))
                            .label("images")
                    )
                    .group_by(LogbookImages.logbook_id_entry)
                    .subquery()
                )

                logbook_entry_case = case(
                    (
                        LogbookEntry.id_logbook_entry.is_not(None),
                        func.json_build_object(
                            "id_logbook_entry", LogbookEntry.id_logbook_entry,
                            "truck_license", LogbookEntry.truck_license,
                            "driver", LogbookEntry.name_driver,
                            "user", LogbookEntry.created_by,
                            "name_user", LogbookEntry.name_user,
                            "quantity", LogbookEntry.quantity,
                            "dni_driver", LogbookEntry.dni_driver,
                        )
                    ),
                    else_=None
                ).label("logbook_entry")

                stmt = (
                    select(
                        PurchaseOrderReceipts,
                        # PurchaseOrder,
                        # StatusPurchaseOrder.name.label("status_name"),
                        func.coalesce(receipts_images_subq.c.images, cast([], ARRAY(Text)).label("images")),
                        logbook_entry_case
                    )
                    # .outerjoin(
                    #     PurchaseOrder,
                    #     PurchaseOrder.id_order == PurchaseOrderReceipts.purchase_order_id
                    # )
                    # .outerjoin(
                    #     StatusPurchaseOrder,
                    #     StatusPurchaseOrder.id_status == PurchaseOrder.status_id
                    # )
                    .outerjoin(receipts_images_subq, receipts_images_subq.c.logbook_entry_id == PurchaseOrderReceipts.logbook_entry_id)
                    .outerjoin(LogbookEntry, LogbookEntry.id_logbook_entry == PurchaseOrderReceipts.logbook_entry_id)
                    .order_by(PurchaseOrderReceipts.created_at.desc())
                )

                # if filters.get("purchase_order_id"):
                #     stmt = stmt.where(PurchaseOrderReceipts.purchase_order_id.in_(filters.get("purchase_order_id")))

                if filters.get("user"):
                    stmt = stmt.where(LogbookEntry.created_by == filters.get("user"))

                if filters.get("without_order"):
                    stmt = stmt.where(PurchaseOrderReceipts.purchase_order_id == None)

                rows = session.execute(stmt).all()
                
                orders = [
                    {
                        "id_receipts": c.id_receipts,
                        "purchase_order_id": c.purchase_order_id,
                        "converted_amount": c.converted_amount,
                        "created_at": c.created_at,
                        "images": images,
                        "logbook_entry": logbook_entry
                        # "purchase_order": {
                        #     "id_order": purchase_order.id_order,
                        #     "status_id": purchase_order.status_id,
                        #     "status_name": status_name,
                        #     "start_date": purchase_order.start_date,
                        #     "end_date": purchase_order.end_date,
                        #     "number_order": purchase_order.number_order,
                        #     "type_order": purchase_order.type_order,
                        #     "quantity": purchase_order.quantity,
                        #     "provider": purchase_order.provider,
                        #     "observations": purchase_order.observations,
                        #     "created_at": purchase_order.created_at,
                        #     "updated_at": purchase_order.updated_at,
                        #     "created_by": purchase_order.created_by,
                        #     "updated_by": purchase_order.updated_by,
                        # }
                    }
                    for c, images, logbook_entry in rows
                ]

                return orders

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al obtener en la base de datos", 500)


    def post_order_receipts(self, session, body, internal, external) -> None:
        try:
            order_receipts = PurchaseOrderReceipts(
                purchase_order_id=body.get('purchase_order_id'),
                logbook_entry_id=body['logbook_entry_id'],
            )

            if order_receipts.purchase_order_id:
                # Validación previa de existencia + status antes de calcular converted_amount
                purchase_order_exists = session.execute(
                    select(PurchaseOrder)
                    .where(PurchaseOrder.id_order == order_receipts.purchase_order_id)
                ).scalar_one_or_none()

                if not purchase_order_exists:
                    raise CustomAPIException(message="No existe la orden de compra", status_code=404)

                if purchase_order_exists.status_id == 2:
                    raise CustomAPIException(message="La orden de compra ya se encuentra completada", status_code=400)

                if purchase_order_exists.type_order == 'BALANCEADO':
                    order_receipts.converted_amount = Decimal(str(body['quantity'])) * Decimal("25")
                else:
                    order_receipts.converted_amount = body['quantity']

            session.add(order_receipts)
            session.flush()

            if order_receipts.purchase_order_id:
                self.calculate_purchase_order(
                    session,
                    order_receipts.purchase_order_id,
                    body['user']
                )

        except OSError as e:
            if e.errno == 36:
                raise CustomAPIException("Nombre de archivo demasiado largo", 400)
            
        except Exception as exception:
            session.rollback()
            logger.error('Error: {}', str(exception), internal=internal, external=external)
            if isinstance(exception, CustomAPIException):
                raise exception
            
            raise CustomAPIException("Error al insertar en la base de datos", 500)

        
    def get_reason_restricition(self, filters, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(ReasonRestriction)
                    .order_by(
                        case(
                            (ReasonRestriction.reason == "Otro", 1),
                            else_=0
                        ),
                        ReasonRestriction.created_at.desc()
                    )
                )
                
                blacklist = [
                    {
                        "id_reason": c.id_reason,
                        "reason": c.reason,
                        "created_at": c.created_at,
                        "created_by": c.created_by,
                    }
                    for c in result.scalars().all()
                ]
                return blacklist
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al obtener en la base de datos", 500)
            

    def get_order_summary(self, filters, internal, external):
        with self.db.session_factory() as session:
            try:
                filters_stmt = []

                if filters.get("destiny_id"):
                    filters_stmt.append(
                        PurchaseOrder.destiny_id.in_(filters.get("destiny_id"))
                    )

                if filters.get("start_date"):
                    filters_stmt.append(PurchaseOrder.created_at >= filters.get("start_date"))

                if filters.get("end_date"):
                    filters_stmt.append(PurchaseOrder.created_at <= filters.get("end_date"))

                join_condition = PurchaseOrder.status_id == StatusPurchaseOrder.id_status

                if filters_stmt:
                    join_condition = and_(join_condition, *filters_stmt)

                status_stmt = (
                    select(
                        StatusPurchaseOrder.id_status,
                        StatusPurchaseOrder.name,
                        func.count(PurchaseOrder.id_order).label("count")
                    )
                    .outerjoin(
                        PurchaseOrder,
                        join_condition
                    )
                    .group_by(
                        StatusPurchaseOrder.id_status,
                        StatusPurchaseOrder.name
                    )
                    .order_by(StatusPurchaseOrder.id_status)
                )

                status_rows = session.execute(status_stmt).all()

                # ------------------------
                # Conteo por tipo
                # ------------------------
                types_stmt = (
                    select(
                        # Cantidad de órdenes
                        func.sum(
                            case(
                                (PurchaseOrder.type_order == "BALANCEADO", 1),
                                else_=0
                            )
                        ).label("balanceado"),

                        func.sum(
                            case(
                                (PurchaseOrder.type_order == "COMBUSTIBLE", 1),
                                else_=0
                            )
                        ).label("combustible"),

                        # Sumatoria de toneladas
                        func.sum(
                            case(
                                (PurchaseOrder.type_order == "BALANCEADO", PurchaseOrder.quantity),
                                else_=0
                            )
                        ).label("quantity_balanceado"),

                        func.sum(
                            case(
                                (PurchaseOrder.type_order == "COMBUSTIBLE", PurchaseOrder.quantity),
                                else_=0
                            )
                        ).label("quantity_combustible"),
                    )
                )

                if filters_stmt:
                    types_stmt = types_stmt.where(and_(*filters_stmt))

                types = session.execute(types_stmt).one()

                return {
                    "status": [
                        {
                            "id_status": row.id_status,
                            "name": row.name,
                            "count": row.count,
                        }
                        for row in status_rows
                    ],
                    "types": {
                        "balanceado": {
                            "count": types.balanceado or 0,
                            "quantity": float(types.quantity_balanceado or 0)
                        },
                        "combustible": {
                            "count": types.combustible or 0,
                            "quantity": float(types.quantity_combustible or 0)
                        }
                    }
                }
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                raise CustomAPIException("Error al obtener el resumen de órdenes", 500)
            

    def get_order_count_by_destiny(self, filters, internal, external):
        with self.db.session_factory() as session:
            try:
                stmt = (
                    select(
                        GroupBusiness.id_group_business,
                        GroupBusiness.name,
                        func.count(PurchaseOrder.id_order).label("count")
                    )
                    .outerjoin(
                        PurchaseOrder,
                        PurchaseOrder.destiny_id == GroupBusiness.id_group_business
                    )
                )

                filters_stmt = []

                if filters.get("destiny_id"):
                    filters_stmt.append(
                        PurchaseOrder.destiny_id.in_(filters.get("destiny_id"))
                    )

                if filters.get("start_date"):
                    filters_stmt.append(
                        PurchaseOrder.created_at >= filters.get("start_date")
                    )

                if filters.get("end_date"):
                    filters_stmt.append(
                        PurchaseOrder.created_at <= filters.get("end_date")
                    )

                if filters_stmt:
                    stmt = stmt.where(and_(*filters_stmt))

                stmt = (
                    stmt.group_by(
                        GroupBusiness.id_group_business,
                        GroupBusiness.name
                    )
                    .order_by(GroupBusiness.name)
                )

                rows = session.execute(stmt).all()

                return [
                    {
                        "id_destiny": row.id_group_business,
                        "name": row.name,
                        "count": row.count
                    }
                    for row in rows
                ]

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                raise CustomAPIException("Error al obtener el conteo por destino", 500)
            

    def delete_blacklist(self, id_blacklist, internal, external):
        with self.db.session_factory() as session:
            try:
                blacklist_exist = session.execute(
                    select(BlacklistDrivers).where(
                        BlacklistDrivers.id_blacklist == id_blacklist
                    )
                ).scalar_one_or_none()

                if not blacklist_exist:
                    raise CustomAPIException(message="No existe el registro", status_code=404)

                session.delete(blacklist_exist)
                session.commit()
                self.delete_image(blacklist_exist.image_path)
            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)

                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al eliminar el registro en la base de datos", 500)
            
    def calculate_purchase_order(self, session, purchase_order_id, user)-> None:
        """
        Recalcula remaining_quantity y status_id de una purchase_order
        en base a la suma de converted_amount de todos sus receipts.
        Debe llamarse dentro de una transacción ya abierta (no hace commit).
        """
        purchase_order_exists = session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.id_order == purchase_order_id)
            .with_for_update()
        ).scalar_one_or_none()

        if not purchase_order_exists:
            raise CustomAPIException(message="No existe la orden de compra", status_code=404)

        if purchase_order_exists.status_id == 2:
            raise CustomAPIException(message="La orden de compra ya se encuentra completada", status_code=400)

        total_quantity = session.execute(
            select(
                func.coalesce(func.sum(PurchaseOrderReceipts.converted_amount), 0)
            ).where(
                PurchaseOrderReceipts.purchase_order_id == purchase_order_id
            )
        ).scalar_one()

        remaining_quantity = purchase_order_exists.quantity - total_quantity

        status_name = "Incompleto"
        if total_quantity == purchase_order_exists.quantity:
            status_name = "Completado"
        elif total_quantity > purchase_order_exists.quantity:
            status_name = "Con Novedad"

        status = session.execute(
            select(StatusPurchaseOrder).where(StatusPurchaseOrder.name == status_name)
        ).scalar_one_or_none()

        if not status:
            raise CustomAPIException(
                message=f"No existe el estado {status_name}",
                status_code=404
            )

        purchase_order_exists.remaining_quantity = remaining_quantity
        purchase_order_exists.status_id = status.id_status
        purchase_order_exists.updated_at = datetime.now()
        purchase_order_exists.updated_by = user
        session.add(purchase_order_exists)

        return purchase_order_exists
    

    def assign_order_to_receipt(self, body: AssignOrderData, internal, external) -> None:
        with self.db.session_factory() as session:
            try:
                receipt = session.execute(
                    select(PurchaseOrderReceipts)
                    .where(PurchaseOrderReceipts.id_receipts == body.id_receipt)
                    .with_for_update()
                ).scalar_one_or_none()

                if not receipt:
                    raise CustomAPIException(message="No existe el receipt", status_code=404)

                if receipt.purchase_order_id is not None:
                    raise CustomAPIException(
                        message="Este receipt ya tiene una orden asignada",
                        status_code=400
                    )
                
                logbook_entry = session.execute(
                    select(LogbookEntry)
                    .where(LogbookEntry.id_logbook_entry == receipt.logbook_entry_id)
                ).scalar_one_or_none()

                if not logbook_entry:
                    raise CustomAPIException(message="No existe la bitácora de ingreso", status_code=404)

                purchase_order = session.execute(
                    select(PurchaseOrder).where(PurchaseOrder.id_order == body.id_purchase_order)
                ).scalar_one_or_none()

                if not purchase_order:
                    raise CustomAPIException(message="No existe la orden de compra", status_code=404)

                if purchase_order.status_id == 2:
                    raise CustomAPIException(message="La orden de compra ya se encuentra completada", status_code=400)

                # Recalcular converted_amount ahora que sabemos el tipo de orden
                if purchase_order.type_order == 'BALANCEADO':
                    receipt.converted_amount = Decimal(str(logbook_entry.quantity)) * Decimal("25")
                else:
                    receipt.converted_amount = logbook_entry.quantity

                receipt.purchase_order_id = body.id_purchase_order
                session.add(receipt)
                session.flush()

                self.calculate_purchase_order(
                    session, body.id_purchase_order, body.user
                )

                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                raise CustomAPIException("Error al reasignar la orden", 500)