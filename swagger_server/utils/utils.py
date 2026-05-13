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

PREFIX_RE = re.compile(
    r'^(Ing\.?|Dr\.?|Dra\.?|Sr\.?|Sra\.?|Tnt\.?|Tte\.?|Cap\.?|Crnel\.?|Arq\.?|Eco\.?)\s+',
    re.IGNORECASE,
)

CONTACTS_BY_CLIENT: dict[str, list[str]] = {
    'Achibros': ['Carlos José Achi', 'Danny Delgado'],
    'Acuamarcruz': ['Alejandro Cruz'],
    'Acvipac': ['Gabriela Romero'],
    'Adelca': ['Edguin Mosquera'],
    'Agripac': ['Bruno Cerezo'],
    'Aifa': ['Héctor Quinteros', 'Daniel Espinoza'],
    'Ana Brito': ['Ana Brito'],
    'Anisaleo': ['Juan Paulo Maruri'],
    'Antes Nicovita': ['Johnny Garcia'],
    'Aq1': ['Jerrie Jalon', 'Eduardo Huren'],
    'Aquagen': ['Luís Francisco Burgos', 'Marlon Martínez'],
    'Aqualitoral': ['Nicolás Pesantez', 'Andrés Guerrero'],
    'Aray': ['Juan José Saab'],
    'Arrocera La Palma': ['Isidro Calderon'],
    'Asoc Camararoneros Puna': ['Pablo Perez'],
    'Avicacompany': ['Alex Cabrera'],
    'Barrecallebaut': ['Karen Cortez', 'Kevin Jativa'],
    'Bellitec': ['Héctor Madero', 'Miguel Aguilar', 'Oswaldo Borja', 'Johana Farah'],
    'Biomar': ['Dick Aguilar', 'Enrique Romero', 'Manuel Orellana'],
    'Bohman': ['Ruben Ramirez'],
    'Boludcorp': ['Ana Moreno'],
    'Brumesa': ['Armando Maza'],
    'Caamronera': ['Francisco Parra', 'Milton Paredes'],
    'Cahusa': ['Ricardo Menéndez'],
    'Camajose': ['Jose Gonzalez', 'José González'],
    'Camarimp': ['Franklin Contreras'],
    'Camaron Mar': ['Andrés Botero'],
    'Camarondeli': ['Jorge Pazmiño'],
    'Camaronera Esmeralda': ['Daniel Aguilera'],
    'Camaronera Puna': ['Andres Ruiz'],
    'Camaronera Rapasinc': ['Freddy Chiang'],
    'Camaronera San Vicente': ['Silvio Andrade', 'Silvia Macias'],
    'Camaronera Taleb': ['Henrry Taleb'],
    'Camaronera Taura': ['David Villalobos'],
    'Camaronero': ['Ernesto Vera Bernabe'],
    'Camaronmar': ['Andrés Botero'],
    'Campamento Victoria': ['Luigi Purizaga'],
    'Cargill': ['Geovanny Villamar', 'Ivanna Aguilar'],
    'Ceibos Procolinas': ['Danilo Pozo'],
    'Cepec': ['Leonardo Mosquera'],
    'Cofimar': ['Erwin Andre', 'Francisco Pesantes'],
    'Comexport': ['Deniss Arévalo', 'Álvaro Villalba'],
    'Construdipro Mallorca': ['Elicio Chiriboga', 'Christian Galarza'],
    'Corporacion Lanec': ['Cristóforo', 'Darwin Pincay', 'Danny Velez', 'Federico Estupiñan', 'Paul Olsen', 'Renzo Olsen'],
    'Crisomar': ['Bastian Hurtado'],
    'Culsaro': ['Luis Pilay', 'Ricardo Zambrano'],
    'Dbfshrimp': ['Gannio Dumes'],
    'Ecuaquimica': ['Juan Pablo Padilla', 'Nelson Yepez', 'David Vaca'],
    'Equitransa': ['Hector Catagua'],
    'Escuvi': ['Fabricio Ferreti'],
    'Expalsa': ['Aldo Centanaro', 'Jose Vite', 'Keyla Branque', 'Rafael Avila', 'Sebastian Malo'],
    'Farmagro': ['Cesar Carpio', 'Cristhian Steiner'],
    'Filacas': ['Ricardo Menendez'],
    'Fimasa': ['Luis Burgos', 'Marlon Martínez', 'José Chala'],
    'Forquarz': ['Humberto Lopez'],
    'Grupo Almar': ['Daniel Flores', 'Marcelo Villareal'],
    'Grupo Champmar': ['Ezequiel Alfonseca', 'Felix Freire', 'Juan Pablo Guerrero'],
    'Grupo Espinoza: Acuataura': ['Diana Pinela'],
    'Grupo Fajardo': ['Karla Iturralde'],
    'Grupo Pino': ['Alvaro Pino', 'Álvaro Pino', 'Alberto Pino', 'Jorge Robalino', 'Cesar Acosta'],
    'Grupo Santos': ['Yulexy Perez', 'Yulexi Perez'],
    'Grupo Varsa': ['Cristian Mendoza'],
    'Grupo Vasco': ['Cristian Mendoza', 'Bryan Valarezo', 'Mathias Egugerin'],
    'Hacienda Palo Santo': ['Manuel Moron'],
    'Hcda Victoria': ['Harry Olsen'],
    'Hotel Wyndham Manta': ['David Guijarro'],
    'Impala Terminal': ['Bryron Vivanco', 'Byron Vivanco'],
    'Impala Terminals': ['Byron Vivanco'],
    'Indurama': ['Gustavo Torres'],
    'Ingenio La Troncal': ['Bruno Moreno'],
    'Ingenio San Carlos': ['Alexis Macías', 'Patricio Vallejo'],
    'Intercia Inmaconsa': ['Tanya Gonzales'],
    'Iriscorp': ['Henrry Palacios'],
    'Junta Beneficiencia De Gye': ['Yander Daniel Cano Menéndez'],
    'La Chola': ['Guillermo Zambrano'],
    'La Fabril': ['Jhon Borbor Vivero', 'Nataly Marchan'],
    'Lan Harris': ['Dan Palau'],
    'Lanec Costa': ['Federico Estupiñan'],
    'Lanec Taura': ['Willyam Martinez'],
    'Lukmar': ['Marco Loza', 'Marcos Loza', 'Salvador Briz'],
    'Magic Flower': ['Esteban Saenz'],
    'Malabrigo - Forquarts': ['Humberto Lopez'],
    'Maquirental': ['Aurelio Panchana'],
    'Marco Castillo': ['Marco Castillo'],
    'Marprovelsa': ['William Jordán', 'George Prado'],
    'Mars': ['Fernando Castro'],
    'Metabaz': ['Guillermo Garcia', 'Guillermo García'],
    'Molino Champion': ['Daniel Pintado'],
    'Muebles El Bosque': ['Darwin Pisco'],
    'Naturisa': ['Ricardo Sola Jr'],
    'Novocentro': ['Fiorella Mendoza'],
    'Numa': ['Nicolás Romero'],
    'Obrythor -Tauramar - Camartua': ['Robert Conforme'],
    'Obrytror': ['Xavier Farah'],
    'Omarsa': ['Carlos Franco', 'Euclides Bozada', 'Gerardo Chavez', 'Jorge Segovia', 'Juan Franco', 'Luis Piguave', 'Maria Eugenia Procel', 'Scott Dally'],
    'Pacifican Taura': ['Jimmy Gotaire'],
    'Palmaplast': ['Freddy Angel'],
    'Pesalmar': ['Juan Carlos Mejía'],
    'Pescasol': ['Jorge Santos', 'Nadia Arteaga'],
    'Pesquesol': ['Yeo Suong'],
    'Pesquesol - Contorto': ['Nadia Arreaga'],
    'Pinturas Unidas': ['Alberto Espinoza'],
    'Planta Durancocoa': ['Ricardo Zambrano'],
    'Procolinas': ['Pablo Corozo'],
    'Promarisco': ['Cristian Cespedes'],
    'Promariscos': ['Fernando Cabrera'],
    'Provexpo': ['Wilfrido Cardenas'],
    'Pycca': ['Darwin Huayamave'],
    'Santa Priscila': ['Cristian Correa'],
    'Seagate': ['Elias Neme', 'Elías Neme', 'Alberto Bustamante'],
    'Songa': ['Franklin Mosquera', 'Mario Villalta'],
    'Stonmelcorp': ['Rolando Quinde'],
    'Tld Terminal Logístico Durán': ['Fabián Prieto', 'Cristian Preciado'],
    'Tropac': ['Marcos Garnica'],
    'Tumbes Pa': ['Ernesto Quiroz'],
}


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
