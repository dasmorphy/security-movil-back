from datetime import date, datetime, time, timedelta
from pytz import timezone
import re

from sqlalchemy import or_

from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.logbook_out import LogbookOut

# Funciones de utilidad para el sistema completo.

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

SEARCH_COLUMNS_OUT = [
    LogbookOut.name_user,
    LogbookOut.name_driver,
    LogbookOut.truck_license,
    LogbookOut.shipping_guide,
    LogbookOut.observations,
    LogbookOut.authorized_by,
    LogbookOut.destiny,
]

SEARCH_COLUMNS_ENTRY = [
    LogbookEntry.name_user,
    LogbookEntry.name_driver,
    LogbookEntry.truck_license,
    LogbookEntry.shipping_guide,
    LogbookEntry.observations,
    LogbookEntry.authorized_by,
    LogbookEntry.destiny_intern,
]


def format_uri_connection(connection):
    return connection["DRIVER"] \
        + "+" \
        + connection["LIBRARY"] \
        + "://" \
        + connection["USER"] \
        + ":" \
        + connection["PASSWORD"] \
        + "@" \
        + connection["HOST"] \
        + ":" \
        + connection["PORT"] \
        + "/" \
        + connection["DB"]


def filter_dict(dict, fields):
    # Filtra el diccionario entrante, retornando nuevo diccionario
    # sólo con los campos definidos y descartando los demás.

    filtered_dict = {}

    for key in dict:

        if key in fields:
            filtered_dict[key] = dict[key]

    return filtered_dict


def format_date(datetime):
    # Retorna una representación en String de una fecha/hora dada.

    return datetime.strftime(DATE_FORMAT)


def get_current_datetime():
    # Retorna la fecha actual en su correspondiente timezone

    return datetime.now(timezone('America/Guayaquil'))


def check_email(email):
    """
    Valida el email

    Args:
        email (String): correo electronico

    Returns:
        True or False si mail es valido o invalido
    """
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (re.fullmatch(regex, email)):
        return True
    else:
        return False
    
def get_date_range(fecha_inicio=None, fecha_fin=None):
    if fecha_inicio and fecha_fin:
        return fecha_inicio, fecha_fin

    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)

    return start, end

def get_workday() -> str :
    now = datetime.now().time()

    if time(7, 0) <= now < time(19, 0):
        return "Diurna"
    else:
        return "Nocturna"

def parse_filters(headers, params):
    groups = headers.get("groups-business-id")
    sectors = headers.get("sectors")
    workday = headers.get("workday")
    category_ids = headers.get("ids-categories")
    return {
        "user": headers.get("user"),
        "groups_business_id": [int(x) for x in groups.split(",")] if groups else [],
        "start_date": params.get("start_date"),
        "end_date": params.get("end_date"),
        "sector_id": [int(x) for x in sectors.split(",")] if sectors else [],
        "category_ids": [int(x) for x in category_ids.split(",")] if category_ids else [],
        "workday": [x for x in workday.split(",")] if workday else [],
        "id_business": params.get("id_business"),
        "notCategory": headers.get("notCategory"),
        "search": params.get("search", "").strip() or None,
    }

def apply_search(filters: list, search: str, columns: list):
    """Agrega un OR con ILIKE sobre todas las columnas especificadas."""
    if not search:
        return
    
    term = f"%{search}%"
    filters.append(
        or_(*[col.ilike(term) for col in columns])
    )

def diference_time(logbook_entry, logbook_out):

    try:
        date_entry = logbook_entry.created_at
        date_out = logbook_out.created_at

        # Diferencia
        difference = date_out - date_entry

        total_seconds = int(difference.total_seconds())

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        return f"{days}d {hours}h {minutes}m"
    
    except Exception as exp:
        print(exp)
        return None


def serialize_out(out, group_name, id_sector, name_sector, name_category, images_out):
    if out is None:
        return None
    return {
        "id_logbook_out": out.id_logbook_out,
        "unity_id": out.unity_id,
        "category_id": out.category_id,
        "name_user": out.name_user,
        "group_name": group_name,
        "group_business_id": out.group_business_id,
        "shipping_guide": out.shipping_guide,
        "quantity": out.quantity,
        "weight": out.weight,
        "truck_license": out.truck_license,
        "name_driver": out.name_driver,
        "lat": out.lat,
        "long": out.long,
        "person_withdraws": out.person_withdraws,
        "destiny": out.destiny,
        "authorized_by": out.authorized_by,
        "observations": out.observations,
        "created_at": out.created_at,
        "updated_at": out.updated_at,
        "created_by": out.created_by,
        "updated_by": out.updated_by,
        "workday": out.workday,
        "id_sector": id_sector,
        "name_sector": name_sector,
        "name_category": name_category,
        "images_out": images_out or [],
        "status": "Finalizado"
    }
