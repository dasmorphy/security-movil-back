

from datetime import datetime, timedelta
from typing import List
from unittest import result
from flask import json
from loguru import logger
from sqlalchemy import ARRAY, DateTime, Integer, String, Text, and_, cast, exists, func, insert, literal, or_, select, true, union_all
from sqlalchemy.orm import aliased
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.authorized import Authorized
from swagger_server.models.db.business import Business
from swagger_server.models.db.business import Business
from swagger_server.models.db.destiny_intern import DestinyIntern
from swagger_server.models.db.employee_intern import EmployeeIntern
from swagger_server.models.db.employee_movement import EmployeeMovement
from swagger_server.models.db.employee_movement_image import EmployeeMovementImage
from swagger_server.models.db.group_business import GroupBusiness
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.category import Category
from swagger_server.models.db.logbook_images import LogbookImages
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.db.report_generated import ReportGenerated
from swagger_server.models.db.request_idempotency import RequestIdempotency
from swagger_server.models.db.sector import Sector
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.models.update_status_employee_data import UpdateStatusEmployeeData
from swagger_server.repository.logbook_repository import LogbookRepository
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

class EmployeeRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")
        self.redis_client = RedisClient()
        self.logbook_repository = LogbookRepository()


    def post_employee_intern(self, employee_body: EmployeeIntern, files, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/employee-intern"
                )
                
                self.logbook_repository.request_idempotency(session, data_request, internal, external)

                existing_employee = session.execute(
                    select(EmployeeIntern).where(
                        EmployeeIntern.dni == employee_body.dni
                    )
                ).scalar_one_or_none()

                if existing_employee:
                    raise CustomAPIException(
                        message=f"Ya existe un empleado registrado con la cédula {employee_body.dni}",
                        status_code=400
                    )

                group_business_exists = session.execute(
                    select(GroupBusiness).where(
                        GroupBusiness.id_group_business == employee_body.group_business_id
                    )
                ).scalar_one_or_none()
                
                if not group_business_exists:
                    raise CustomAPIException(
                        message="No existe el grupo de negocio",
                        status_code=404
                    )
                
                
                #Guardar imágenes (máx 10)
                if files:
                    result = self.logbook_repository.save_image(files[0], name_folder="employees")
                    saved_files.append(result["url"])
                    employee_body.photo = result["url"]

                session.add(employee_body)
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


    def get_employees_intern(self, filters: dict, internal, external) -> List[EmployeeIntern]:
        with self.db.session_factory() as session:
            try:
                last_movement_subquery = (
                    select(EmployeeMovement.type_movement)
                    .where(EmployeeMovement.employee_id == EmployeeIntern.id_employee)
                    .order_by(EmployeeMovement.created_at.desc())
                    .limit(1)
                    .scalar_subquery()
                )

                query = (
                    select(
                        EmployeeIntern,
                        GroupBusiness.name.label("group_name"),
                        last_movement_subquery.label("last_type_movement")
                    )
                    .join(
                        GroupBusiness,
                        GroupBusiness.id_group_business == EmployeeIntern.group_business_id
                    )
                    .order_by(EmployeeIntern.created_at.desc())
                )

                if filters.get("id_employee"):
                    query = query.where(EmployeeIntern.id_employee == filters["id_employee"])

                if filters.get("type_movement"):
                    query = query.where(
                        last_movement_subquery == filters["type_movement"]
                    )

                # if filters.get("groups_business_id"):
                #     query = query.where(EmployeeIntern.group_business_id.in_(filters["groups_business_id"]))

                if filters.get("start_date"):
                    start_date = datetime.strptime(filters["start_date"], "%Y-%m-%d")
                    query = query.where(EmployeeIntern.created_at >= start_date)

                if filters.get("end_date"):
                    end_date = datetime.strptime(filters["end_date"], "%Y-%m-%d")
                    query = query.where(EmployeeIntern.created_at <= end_date)

                result = session.execute(query)
                rows = result.all()
                return rows

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def post_employee_movement(self, employee_movement_body: EmployeeMovement, images, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/employee-movement"
                )
                
                self.logbook_repository.request_idempotency(session, data_request, internal, external)

                employee_exists = session.execute(
                    select(EmployeeIntern).where(
                        EmployeeIntern.id_employee == employee_movement_body.employee_id
                    )
                ).scalar_one_or_none()

                if not employee_exists:
                    raise CustomAPIException(
                        message="El empleado especificado no existe",
                        status_code=404
                    )
                
                if employee_movement_body.group_business_id:
                    group_business_exists = session.execute(
                        select(GroupBusiness).where(
                            GroupBusiness.id_group_business == employee_movement_body.group_business_id
                        )
                    ).scalar_one_or_none()
                    
                    if not group_business_exists:
                        raise CustomAPIException(
                            message="No existe el grupo de negocio",
                            status_code=404
                        )

                if employee_movement_body.authorized_id:
                    authorized_exists = session.execute(
                        select(Authorized).where(
                            Authorized.id_authorized == employee_movement_body.authorized_id
                        )
                    ).scalar_one_or_none()
                    
                    if not authorized_exists:
                        raise CustomAPIException(
                            message="El autorizado especificado no existe",
                            status_code=404
                        )
                    
                session.add(employee_movement_body)
                session.flush()

                movement_id = employee_movement_body.id_movement

                #Guardar imágenes (máx 10)
                for file in images[:10]:
                    result = self.logbook_repository.save_image(file, "employees")
                    saved_files.append(result["url"])

                    image = EmployeeMovementImage(
                        employee_movement_id=movement_id,
                        image_path=result["url"]
                    )

                    session.add(image)

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

    def get_employees_movement(self, filters: dict, internal, external) -> List:
        with self.db.session_factory() as session:
            try:
                # ── Subquery de imágenes ENTRY ────────────────────────────────
                images_movement_subq = (
                    select(
                        EmployeeMovementImage.employee_movement_id.label("movement_id"),
                        func.array_agg(EmployeeMovementImage.image_path)
                            .filter(EmployeeMovementImage.image_path.isnot(None))
                            .label("images")
                    )
                    .group_by(EmployeeMovementImage.employee_movement_id)
                    .subquery()
                )

                query = select(
                    EmployeeMovement,
                    EmployeeIntern,
                    GroupBusiness.name.label("group_name"),
                    func.coalesce(images_movement_subq.c.images, cast([], ARRAY(Text))).label("images"),
                ).join(
                    EmployeeIntern,
                    EmployeeIntern.id_employee == EmployeeMovement.employee_id,
                ).outerjoin(
                    GroupBusiness,
                    GroupBusiness.id_group_business == EmployeeMovement.group_business_id
                ).outerjoin(
                    images_movement_subq, 
                    images_movement_subq.c.movement_id == EmployeeMovement.id_movement
                ).order_by(EmployeeMovement.created_at.desc())


                # Aplicar filtros
                if filters.get("start_date"):
                    start_date = datetime.strptime(filters["start_date"], "%Y-%m-%d")
                    query = query.where(EmployeeMovement.created_at >= start_date)

                if filters.get("end_date"):
                    end_date = datetime.strptime(filters["end_date"], "%Y-%m-%d")
                    query = query.where(EmployeeMovement.created_at <= end_date)

                if filters.get("id_employee"):
                    query = query.where(EmployeeMovement.employee_id == filters["id_employee"])

                if filters.get("status_employee"):
                    query = query.where(EmployeeIntern.status == filters["status_employee"])

                if filters.get("group_business_id"):
                    company_ids = filters["group_business_id"]

                    query = query.where(
                        or_(
                            EmployeeMovement.group_business_id.in_(company_ids),
                            and_(
                                EmployeeMovement.destiny_id.in_(company_ids),
                                EmployeeMovement.type_movement == "TRANSFER"
                            )
                        )
                    )

                if filters.get("type_movement"):
                    query = query.where(EmployeeMovement.type_movement == filters["type_movement"])
                
                result = session.execute(query)
                rows = result.all()

                return rows
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def update_employee_intern_status(self, id_employee_intern: int, data: UpdateStatusEmployeeData, internal_process) -> None:
        internal, external = internal_process
        status = data.status
        user_update = data.user_update

        with self.db.session_factory() as session:
            try:
                # Verificar que el empleado existe
                employee_exists = session.execute(
                    select(EmployeeIntern).where(
                        EmployeeIntern.id_employee == id_employee_intern
                    )
                ).scalar_one_or_none()

                if not employee_exists:
                    raise CustomAPIException(
                        message="El personal no existe",
                        status_code=404
                    )

                # Actualizar el status
                employee_exists.status = status
                employee_exists.updated_by = user_update
                employee_exists.updated_at = datetime.now()
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al actualizar en la base de datos", 500)

            finally:
                session.close()


    def get_count_movements(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                filters = true()

                if filtersBase.get("user"):
                    filters = and_(
                        filters,
                        EmployeeMovement.created_by == filtersBase.get("user")
                    )

                if filtersBase.get("start_date"):
                    filters = and_(
                        filters,
                        EmployeeMovement.created_at >= filtersBase.get("start_date")
                    )

                if filtersBase.get("end_date"):
                    filters = and_(
                        filters,
                        EmployeeMovement.created_at <= filtersBase.get("end_date")
                    )

                if filtersBase.get("group_business"):
                    filters = and_(filters, EmployeeMovement.group_business_id.in_(filtersBase.get("group_business")))

                stmt = (
                    select(
                        EmployeeMovement.type_movement,
                        func.count().label("count")
                    )
                    .where(filters)
                    .group_by(EmployeeMovement.type_movement)
                )

                result = session.execute(stmt).all()

                data = [
                    {
                        "type_movement": row.type_movement,
                        "count": row.count
                    }
                    for row in result
                ]

                # Total general
                total = sum(item["count"] for item in data)

                # Agregar porcentaje
                for item in data:
                    percentage = (
                        (item["count"] / total) * 100
                        if total > 0 else 0
                    )

                    item["percentage"] = round(percentage)

                return data

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)

                if isinstance(exception, CustomAPIException):
                    raise exception

                raise CustomAPIException("Error al obtener el conteo de ingresos en la base de datos", 500)