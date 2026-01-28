from datetime import date, datetime, timedelta
from pytz import timezone
import re

# Funciones de utilidad para el sistema completo.

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


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
