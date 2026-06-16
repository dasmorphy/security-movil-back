

import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from io import BytesIO
import os
import urllib.request
import tempfile
import pandas as pd
from typing import Counter
from loguru import logger
from openpyxl import load_workbook
from datetime import datetime

import requests
# from weasyprint import HTML
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.employee_intern import EmployeeIntern
from swagger_server.models.db.employee_movement import EmployeeMovement
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.db.request_idempotency import RequestIdempotency
from swagger_server.models.employee_movement_data import EmployeeMovementData
from swagger_server.models.request_post_logbook_entry import RequestPostLogbookEntry
from swagger_server.models.request_post_logbook_out import RequestPostLogbookOut
from swagger_server.models.update_status_employee_data import UpdateStatusEmployeeData
from swagger_server.repository.employee_repository import EmployeeRepository
from swagger_server.repository.logbook_repository import LogbookRepository
from openpyxl.styles import Font, PatternFill

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Spacer, Image
from collections import OrderedDict, defaultdict

from swagger_server.utils.utils import diference_time, get_workday, parse_filters, serialize_out

from flask import render_template
from xhtml2pdf import pisa

@dataclass
class PaginationParams:
    page: int = 1
    page_size: int = 20

    @property
    def offset(self):
        return (self.page - 1) * self.page_size

class EmployeeUseCase:

    def __init__(self, employee_repository: EmployeeRepository):
        self.employee_repository = employee_repository


    def post_employee_intern(self, body, files, internal, external) -> None:        
        employee = EmployeeIntern(
            dni=body['dni'],
            group_business_id=body['group_business_id'],
            names=body['names'],
            lastname=body['lastname'],
            position=body['position'],
            observations=body['observations'],
            created_by=body.get('user'),
            name_user=body['name_user'],
            updated_by=body.get('user'),
            status="Autorizado"
        )

        self.employee_repository.post_employee_intern(employee, files, internal, external)

    def get_employees_intern(self, headers, params, internal, external):
        groups_business_id = params.get("id_group_business")

        filters = {
            "start_date": params.get("start_date"),
            "end_date": params.get("end_date"),
            "type_movement": params.get("type_movement"),
            "id_employee": params.get("id_employee"),
            "groups_business_id": [
                int(x.strip())
                for x in groups_business_id.split(",")
                if x.strip()
            ] if groups_business_id else [],
        }

        MOVEMENT_STATUS = {
            "CHECK_IN": "Ingreso",
            "TRANSFER": "Movimiento interno",
            "CHECK_OUT": "Salida"
        }
        
        rows = self.employee_repository.get_employees_intern(filters, internal, external)

        results = [
            {
                "id_employee_intern": c.id_employee,
                "dni": c.dni,
                "group_business_id": c.group_business_id,
                "names": c.names,
                "lastname": c.lastname,
                "position": c.position,
                "observations": c.observations,
                "name_user": c.name_user,
                "status": c.status,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "created_by": c.created_by,
                "updated_by": c.updated_by,
                "group_name": group_name,
                "photo": c.photo,
                "last_status_movement": MOVEMENT_STATUS.get(last_type_movement) or "Sin movimientos"
            }
            for c, group_name, last_type_movement in rows
        ]

        return results

    def post_employee_movement(self, body, files, internal, external) -> None:
        employee_movement = EmployeeMovement(
            employee_id=body['employee_id'],
            group_business_id=body.get('group_business_id'),
            destiny_id=body.get('destiny_id'),
            shipping_guide=body.get('shipping_guide'),
            authorized_id=body.get('authorized_id'),
            type_movement=body.get('type_movement'),
            observations=body.get('observations'),
            other_destiny=body.get('other_destiny'),
            reason_out=body.get('reason_out'),
            name_user=body.get('name_user'),
            created_by=body.get('user'),
            updated_by=body.get('user'),
        )

        self.employee_repository.post_employee_movement(employee_movement, files, internal, external)

    def get_employees_movement(self, headers, params, internal, external):
        groups_business_id = params.get("group_business_id")

        filters = {
            "start_date": params.get("start_date"),
            "end_date": params.get("end_date"),
            "type_movement": params.get("type_movement"),
            "id_employee": params.get("id_employee"),
            "destiny_id": params.get("destiny_id"),
            "status_employee": params.get("status_employee"),
            "group_business_id": [
                int(x.strip())
                for x in groups_business_id.split(",")
                if x.strip()
            ] if groups_business_id else [],
        }

        MOVEMENT_STATUS = {
            "CHECK_IN": "Ingreso",
            "TRANSFER": "Movimiento interno",
            "CHECK_OUT": "Salida"
        }
        
        rows = self.employee_repository.get_employees_movement(filters, internal, external)

        results = [
            {
                "id_movement": c[0].id_movement,
                "employee_id": c[0].employee_id,
                "group_business_id": c[0].group_business_id,
                "authorized_id": c[0].authorized_id,
                "type_movement": c[0].type_movement,
                "shipping_guide": c[0].shipping_guide,
                "observations": c[0].observations,
                "destiny_id": c[0].destiny_id,
                "other_destiny": c[0].other_destiny,
                "status": MOVEMENT_STATUS.get(c[0].type_movement),
                "reason_out": c[0].reason_out,
                "name_user": c[0].name_user,
                "created_at": c[0].created_at,
                "updated_at": c[0].updated_at,
                "created_by": c[0].created_by,
                "updated_by": c[0].updated_by,
                "employee_dni": c[1].dni if c[1] else None,
                "employee_names": c[1].names if c[1] else None,
                "employee_status": c[1].status if c[1] else None,
                "employee_lastname": c[1].lastname if c[1] else None,
                "group_name": c[2] if c[2] else None,
                "images": c[3] or [],
            }
            for c in rows
        ]

        return results

    def update_employee_intern_status(self, id_employee_intern: int, data: UpdateStatusEmployeeData, internal_process) -> None:
        self.employee_repository.update_employee_intern_status(id_employee_intern, data, internal_process)