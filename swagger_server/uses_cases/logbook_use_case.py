

import os
from openpyxl import load_workbook
from datetime import datetime
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.request_post_logbook_entry import RequestPostLogbookEntry
from swagger_server.models.request_post_logbook_out import RequestPostLogbookOut
from swagger_server.repository.logbook_repository import LogbookRepository


class LogbookUseCase:

    def __init__(self, logbook_repository: LogbookRepository):
        self.logbook_repository = logbook_repository

    def post_logbook_entry(self, body: RequestPostLogbookEntry, internal, external) -> None:
        logbook_entry = LogbookEntry(
            unity_id=body.logbook_entry.id_unity,
            category_id=body.logbook_entry.id_category,
            shipping_guide=body.logbook_entry.shipping_guide,
            description=body.logbook_entry.description,
            quantity=body.logbook_entry.quantity,
            weight=body.logbook_entry.weight,
            provider=body.logbook_entry.provider,
            destiny_intern=body.logbook_entry.destiny_intern,
            authorized_by=body.logbook_entry.authorized_by,
            observations=body.logbook_entry.observations,
            created_by=body.logbook_entry.created_by,
            updated_by=body.logbook_entry.created_by
        )

        self.logbook_repository.post_logbook_entry(logbook_entry, internal, external)

    def post_logbook_out(self, body: RequestPostLogbookOut, internal, external) -> None:
        logbook_out = LogbookOut(
            unity_id=body.logbook_out.id_unity,
            category_id=body.logbook_out.id_category,
            shipping_guide=body.logbook_out.shipping_guide,
            quantity=body.logbook_out.quantity,
            weight=body.logbook_out.weight,
            truck_license=body.logbook_out.truck_license,
            name_driver=body.logbook_out.name_driver,
            person_withdraws=body.logbook_out.person_withdraws,
            destiny=body.logbook_out.destiny,
            authorized_by=body.logbook_out.authorized_by,
            observations=body.logbook_out.observations,
            created_by=body.logbook_out.created_by,
            updated_by=body.logbook_out.created_by
        )

        self.logbook_repository.post_logbook_out(logbook_out, internal, external)

    def get_all_categories(self, internal, external):
        return self.logbook_repository.get_all_categories(internal, external)
    
    def get_all_unities(self, internal, external):
        return self.logbook_repository.get_all_unities(internal, external)
    

    def generar_excel(self, datos, output_path):
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(
            BASE_DIR,
            "templates",
            "template_report.xlsx"
        )

        wb = load_workbook(template_path)
        ws = wb.active

        # Cabecera
        ws["C3"] = datos["fecha"]
        ws["C4"] = datos["localidad"]
        ws["C5"] = datos["puesto_control"]
        ws["C6"] = datos["agente"]

        ws["F3"] = datos["ref"]
        ws["F4"] = datos["hora"]

        fila_inicio = 10

        for item in datos["items"]:
            ws[f"C{fila_inicio}"] = item["salida_cant"]
            ws[f"D{fila_inicio}"] = item["salida_unidad"]
            ws[f"E{fila_inicio}"] = item["entrada_cant"]
            ws[f"F{fila_inicio}"] = item["entrada_unidad"]
            fila_inicio += 1

        wb.save(output_path)