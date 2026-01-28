

import os
from openpyxl import load_workbook
from datetime import datetime
from swagger_server.models.db.logbook_entry import LogbookEntry
from swagger_server.models.db.logbook_out import LogbookOut
from swagger_server.models.request_post_logbook_entry import RequestPostLogbookEntry
from swagger_server.models.request_post_logbook_out import RequestPostLogbookOut
from swagger_server.repository.logbook_repository import LogbookRepository
from openpyxl.styles import Font, PatternFill


class LogbookUseCase:

    def __init__(self, logbook_repository: LogbookRepository):
        self.logbook_repository = logbook_repository

    def post_logbook_entry(self, body: RequestPostLogbookEntry, internal, external) -> None:
        logbook_entry = LogbookEntry(
            unity_id=body.logbook_entry.id_unity,
            category_id=body.logbook_entry.id_category,
            group_business_id=body.logbook_entry.id_group_business,
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
            group_business_id=body.logbook_out.id_group_business,
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
    
    def get_all_sector(self, internal, external):
        return self.logbook_repository.get_all_sectores(internal, external)

    def get_user_info(datos):
        return 

    def get_sector_by_id(self, id_sector, internal, external):
        return self.logbook_repository.get_sector_by_id(id_sector, internal, external)


    def generar_excel(self, datos, output_path, internal, external):
        # '2026-01-27 00:00:00', '2026-01-28 00:00:00'
        now = datetime.now()
        date = now.strftime("%d/%m/%Y")
        time = now.strftime("%H:%M:%S")

        logbook_entry_rows = self.logbook_repository.get_logbook_resume(internal, external, LogbookEntry)
        logbook_out_rows = self.logbook_repository.get_logbook_resume(internal, external, LogbookOut)
        # business_user, name_user = self.get_user_info(datos)

        print(logbook_entry_rows)
        print(logbook_out_rows)

        resultado = {}

        for row in logbook_out_rows:
            grupo = row[1]          # GroupBusiness.name
            cat_id = row[2]         # Category.id_category

            if grupo not in resultado:
                resultado[grupo] = {
                    "categorias": {}
                }

            resultado[grupo]["categorias"][cat_id] = {
                "categoria": row[3],
                "unidad": row[5],
                "salida": row[4],
                "entrada": 0
            }


        for row in logbook_entry_rows:
            grupo = row[1]
            cat_id = row[2]

            if grupo not in resultado:
                resultado[grupo] = {
                    "categorias": {}
                }

            if cat_id not in resultado[grupo]["categorias"]:
                resultado[grupo]["categorias"][cat_id] = {
                    "categoria": row[3],
                    "unidad": row[5],
                    "salida": 0,
                    "entrada": row[4]
                }
            else:
                resultado[grupo]["categorias"][cat_id]["entrada"] = row[4]


        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(
            BASE_DIR,
            "templates",
            "template_report.xlsx"
        )

        wb = load_workbook(template_path)
        ws = wb.active

        # ws_copia = wb.copy_worksheet(wb)
        # ws_copia.title = "REPORTE 2"

        # Cabecera
        ws["C7"] = date
        ws["C8"] = datos["localidad"]
        ws["C9"] = datos["puesto_control"]
        ws["C10"] = datos["agente"]
        ws["B14"] = "TAURA (TOTAL)"

        fill = PatternFill(
            start_color="FFFF00",
            end_color="FFFF00",
            fill_type="solid"
        )

        ws["B14"].fill = fill
        ws["B14"].font = Font(bold=True)

        ws["F7"] = datos["ref"]
        ws["F8"] = time

        fila_inicio = 15

        for grupo, data in resultado.items():
            ws[f"B{fila_inicio}"] = grupo.upper()
            ws[f"B{fila_inicio}"].font = Font(bold=True)

            fila_inicio += 1

            for item in data["categorias"].values():
                ws[f"B{fila_inicio}"] = f"TOTAL {item['categoria'].upper()}"
                ws[f"C{fila_inicio}"] = item["salida"]
                ws[f"D{fila_inicio}"] = item["unidad"]
                ws[f"E{fila_inicio}"] = item["entrada"]
                ws[f"F{fila_inicio}"] = item["unidad"]
                
                fila_inicio += 1
            
            fila_inicio += 1

        wb.save(output_path)