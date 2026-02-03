

from typing import List
from unittest import result
from loguru import logger
from sqlalchemy import and_, exists, func, insert, select
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.business import Business
from swagger_server.models.db.business import Business
from swagger_server.models.db.group_business import GroupBusiness
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.category import Category
from swagger_server.models.db.logbook_images import LogbookImages
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.db.report_generated import ReportGenerated
from swagger_server.models.db.sector import Sector
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.resources.databases.postgresql import PostgreSQLClient
from swagger_server.utils.utils import get_date_range
import os
from PIL import Image
from uuid import uuid4
from werkzeug.utils import secure_filename

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

                group_business_exists = session.execute(
                    select(
                        exists().where(
                            GroupBusiness.id_group_business == logbook_entry_body.group_business_id
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
                
                if not group_business_exists:
                    raise CustomAPIException(
                        message="No existe el grupo de negocio",
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

    def post_logbook_out(self, logbook_out_body: LogbookOut, images, internal, external) -> None:
        saved_files = []

        if len(images) > 10:
            raise CustomAPIException("Máximo 10 imagenes", 500)


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

                group_business_exists = session.execute(
                    select(
                        exists().where(
                            GroupBusiness.id_group_business == logbook_out_body.group_business_id
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
                
                if not group_business_exists:
                    raise CustomAPIException(
                        message="No existe el grupo de negocio",
                        status_code=404
                    )
                
                session.add(logbook_out_body)
                session.flush()

                logbook_out_id = logbook_out_body.id

                #Guardar imágenes (máx 10)
                for file in images[:10]:
                    result = self.save_image_as_webp(file)
                    saved_files.append(result["url"])

                    image = LogbookImages(
                        logbook_id_out=logbook_out_id,
                        image_path=result["url"]
                    )

                    session.add(image)

                session.commit()

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
            
    def get_group_business_by_id_business(self, id_business, internal, external):
        with self.db.session_factory() as session:
            try:
                group_business = session.execute(
                    select(GroupBusiness)
                    .where(GroupBusiness.business_id == id_business)
                ).scalars().all()

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
                query = (
                    session.query(
                        Sector.id_sector,
                        Sector.name,
                        Sector.created_at,
                        Sector.updated_at
                    )
                    .join(GroupBusiness, Sector.id_sector == GroupBusiness.sector_id)
                    .join(Business, Business.id_business == GroupBusiness.business_id)
                    .filter(Business.id_business == id_business)
                    .group_by(Sector.id_sector)
                )

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
                        Sector.name.label("name_sector")
                    )
                    .join(
                        GroupBusiness,
                        GroupBusiness.id_group_business == LogbookEntry.group_business_id
                    )
                    .join(
                        Sector,
                        Sector.id_sector == GroupBusiness.sector_id
                    )
                )

                filters = []

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
                        Sector.name.label("name_sector")
                    )
                    .join(
                        GroupBusiness,
                        GroupBusiness.id_group_business == LogbookOut.group_business_id
                    )
                    .join(
                        Sector,
                        Sector.id_sector == GroupBusiness.sector_id
                    )
                )

                filters = []

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

                if filters:
                    stmt = stmt.where(and_(*filters))

                result = session.execute(stmt).all()
                return result

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
                        GroupBusiness.id_group_business,
                        GroupBusiness.name.label("grupo_negocio"),
                        Category.id_category,
                        Category.name_category,
                        func.sum(model.quantity).label("cantidad"),
                        UnityWeight.name.label("unidad"),
                    )
                    .join(Category, Category.id_category == model.category_id)
                    .join(UnityWeight, UnityWeight.id_unity == model.unity_id)
                    .join(GroupBusiness, GroupBusiness.id_group_business == model.group_business_id)
                    .filter(model.created_at >= start)
                    .filter(model.created_at < end)
                    .group_by(
                        GroupBusiness.id_group_business,
                        GroupBusiness.name,
                        Category.id_category,
                        Category.name_category,
                        UnityWeight.name,
                    )
                    .order_by(GroupBusiness.name)
                    .all()
                )
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

    def save_image_as_webp(self, file):
        ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
        ext = file.filename.rsplit(".", 1)[-1].lower()
        folder = f"/var/www/uploads/logbooks"

        if not file or file.filename == "":
            raise ValueError("Archivo inválido")

        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Formato no permitido")

        original_name = secure_filename(file.filename)
        base_name = os.path.splitext(original_name)[0]

        filename = f"{uuid4()}_{base_name}.webp"
        path = os.path.join(folder, filename)

        image = Image.open(file)
        image = image.convert("RGB")  # Evita problemas con PNG

        image.save(
            path,
            "WEBP",
            quality=80,     # 🔥 sweet spot
            method=6        # máxima compresión
        )

        return {
            "url": f"/uploads/logbooks/{filename}"
        }