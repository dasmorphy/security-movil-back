

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
from swagger_server.models.db.employee_intern import EmployeeIntern
from swagger_server.models.db.employee_movement import EmployeeMovement
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

class EmployeeRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")
        self.redis_client = RedisClient()


    def post_employee_intern(self, employee_body: EmployeeIntern, files, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/employee-intern"
                )
                
                self.request_idempotency(session, data_request, internal, external)

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
                    result = self.save_image(files[0], name_folder="employees")
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
                result = session.execute(
                    select(
                        EmployeeIntern,
                        GroupBusiness.name.label("group_name")
                    )
                    .join(
                        GroupBusiness,
                        GroupBusiness.id_group_business == EmployeeIntern.group_business_id
                    )
                )

                rows = result.all()

                return rows
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def post_employee_movement(self, employee_movement_body: EmployeeMovement, files, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                data_request = RequestIdempotency(
                    uuid=external,
                    endpoint="/rest/zent-logbook-api/v1.0/employee-movement"
                )
                
                self.request_idempotency(session, data_request, internal, external)

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
                query = select(
                    EmployeeMovement,
                    EmployeeIntern,
                    GroupBusiness.name.label("group_name")
                ).join(
                    EmployeeIntern,
                    EmployeeIntern.id_employee == EmployeeMovement.employee_id
                ).join(
                    GroupBusiness,
                    GroupBusiness.id_group_business == EmployeeMovement.group_business_id
                )

                # Aplicar filtros
                if filters.get("start_date"):
                    start_date = datetime.strptime(filters["start_date"], "%Y-%m-%d")
                    query = query.where(EmployeeMovement.created_at >= start_date)

                if filters.get("end_date"):
                    end_date = datetime.strptime(filters["end_date"], "%Y-%m-%d")
                    query = query.where(EmployeeMovement.created_at <= end_date)

                if filters.get("type_movement"):
                    query = query.where(EmployeeMovement.type_movement == filters["type_movement"])

                if filters.get("status"):
                    query = query.where(EmployeeMovement.status == filters["status"])

                result = session.execute(query)
                rows = result.all()

                return rows
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)