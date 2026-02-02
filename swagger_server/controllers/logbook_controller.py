from datetime import datetime
from json import JSONEncoder
import os
from timeit import default_timer
import connexion
from flask import jsonify, request, send_file
import six

from flask.views import MethodView

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.request_post_logbook_entry import RequestPostLogbookEntry  # noqa: E501
from swagger_server.models.request_post_logbook_out import RequestPostLogbookOut  # noqa: E501
from swagger_server.models.response_error import ResponseError  # noqa: E501
from swagger_server.models.response_post_logbook_entry import ResponsePostLogbookEntry  # noqa: E501
from swagger_server.models.response_post_logbook_out import ResponsePostLogbookOut  # noqa: E501
from swagger_server import util
from loguru import logger

from swagger_server.repository.logbook_repository import LogbookRepository
from swagger_server.uses_cases.logbook_use_case import LogbookUseCase
from swagger_server.utils.transactions.transaction import generate_internal_transaction_id


class LogbookView(MethodView):
    def __init__(self):
        self.logger = logger
        logbook_repository = LogbookRepository()
        self.logbook_use_case = LogbookUseCase(logbook_repository)

    def post_logbook_entry(self, body=None):  # noqa: E501
        """Guarda la bitacora de ingreso en la base de datos.

        Guardado de bitacora de ingreso # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: ResponsePostLogbookEntry
        """
        internal_process = (None, None)
        function_name = "post_logbook_entry"
        response = {}
        status_code = 500
        try:
            if connexion.request.is_json:
                body = RequestPostLogbookEntry.from_dict(connexion.request.get_json())  # noqa: E501
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = body.external_transaction_id
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {body.channel}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                self.logbook_use_case.post_logbook_entry(body, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Bitácora de ingreso creada correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=body.external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code


    def post_logbook_out(self, body=None):  # noqa: E501
        """Guarda la bitacora de salida en la base de datos.

        Guardado de bitacora de salida # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: GenericResponse
        """
        internal_process = (None, None)
        function_name = "post_logbook_out"
        response = {}
        status_code = 500
        try:
            if connexion.request.is_json:
                body = RequestPostLogbookOut.from_dict(connexion.request.get_json())  # noqa: E501
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = body.external_transaction_id
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {body.channel}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                self.logbook_use_case.post_logbook_out(body, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Bitácora de salida creada correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=body.external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_all_categories(self):
        internal_process = (None, None)
        function_name = "get_all_categories"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                results = self.logbook_use_case.get_all_categories(internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Categorias obtenidas correctamente"
                response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_all_unities(self):
        internal_process = (None, None)
        function_name = "get_all_unities"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                results = self.logbook_use_case.get_all_unities(internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Unidades de peso obtenidas correctamente"
                response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_sector_by_id(self, id_sector):
        internal_process = (None, None)
        function_name = "get_sector_by_id"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                print("ID SECTOR:", id_sector)
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                result = self.logbook_use_case.get_sector_by_id(id_sector, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Sector obtenido correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_all_sector(self):
        internal_process = (None, None)
        function_name = "get_all_sector"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                results = self.logbook_use_case.get_all_sector(internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Sectores obtenidos correctamente"
                response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_sector_by_business(self, id_sector):
        internal_process = (None, None)
        function_name = "get_sector_by_business"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                print("ID SECTOR:", id_sector)
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                result = self.logbook_use_case.get_sector_by_business(id_sector, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Sector obtenido correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    

    def get_group_business_by_id_business(self, id_business):
        internal_process = (None, None)
        function_name = "get_group_business_by_id_business"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                result = self.logbook_use_case.get_group_business_by_id_business(id_business, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Grupos de negocio obtenidos correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_generate_excel(self):
        internal_process = (None, None)
        function_name = "get_generate_excel"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)


                datos = {
                    "fecha": "01/10/2026",
                    "localidad": "TAURA (TOTAL)",
                    "puesto_control": "GARITA DE SEGURIDAD",
                    "agente": "Juan Perez",
                    "ref": "RP2026-010",
                    "hora": "19:00",
                    "business_id": 1,

                    "type_report": "REPORTE DIARIO",
                    "status": "GENERADO",
                    "shipping_error": None,
                    "created_at": datetime.now(),
                    "deadline": datetime.now(),
                    "shipping_date": datetime.now(),
                    "created_by": "Juan Perez",
                    "start_date": datetime.now().replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    ),


                    "items": [
                        {
                            "salida_cant": 0,
                            "salida_unidad": "LIBRAS",
                            "entrada_cant": 0,
                            "entrada_unidad": "LIBRAS"
                        },
                        {
                            "salida_cant": 0,
                            "salida_unidad": "GALONES",
                            "entrada_cant": 1980,
                            "entrada_unidad": "GALONES"
                        }
                    ]
                }
                
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                output = os.path.join(
                    BASE_DIR,
                    "..",
                    "template_report.xlsx"
                )
                self.logbook_use_case.generate_excel(datos, output, internal_transaction_id, external_transaction_id)
                self.logbook_use_case.post_report_generated(datos, internal_transaction_id, external_transaction_id)
                
                # response["error_code"] = 0
                # response["message"] = "Unidades de peso obtenidas correctamente"
                # response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            return response, status_code
            
        return send_file(output, as_attachment=True)
    

    def get_generate_pdf(self):
        internal_process = (None, None)
        function_name = "get_generate_pdf"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)


                datos = {
                    "fecha": "01/10/2026",
                    "localidad": "TAURA (TOTAL)",
                    "puesto_control": "GARITA DE SEGURIDAD",
                    "agente": "Juan Perez",
                    "ref": "RP2026-010",
                    "hora": "19:00",
                    "business_id": 1,

                    "type_report": "REPORTE DIARIO",
                    "status": "GENERADO",
                    "shipping_error": None,
                    "created_at": datetime.now(),
                    "deadline": datetime.now(),
                    "shipping_date": datetime.now(),
                    "created_by": "Juan Perez",
                    "start_date": datetime.now().replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    ),


                    "items": [
                        {
                            "salida_cant": 0,
                            "salida_unidad": "LIBRAS",
                            "entrada_cant": 0,
                            "entrada_unidad": "LIBRAS"
                        },
                        {
                            "salida_cant": 0,
                            "salida_unidad": "GALONES",
                            "entrada_cant": 1980,
                            "entrada_unidad": "GALONES"
                        }
                    ]
                }
                
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                output = os.path.join(
                    BASE_DIR,
                    "..",
                    "template_report.pdf"
                )
                # self.logbook_use_case.generate_excel(datos, output, internal_transaction_id, external_transaction_id)
                # self.logbook_use_case.post_report_generated(datos, internal_transaction_id, external_transaction_id)
                self.logbook_use_case.generate_pdf(datos, output, internal_transaction_id, external_transaction_id)
                
                # response["error_code"] = 0
                # response["message"] = "Unidades de peso obtenidas correctamente"
                # response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            return response, status_code
            
        return send_file(output, as_attachment=True)
    

    
    def get_all_logbook_entry(self):
        internal_process = (None, None)
        function_name = "get_all_logbook_entry"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                result = self.logbook_use_case.get_logbooks_entry(request.headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Bitacoras de entrada obtenidas correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_all_logbook_out(self):
        internal_process = (None, None)
        function_name = "get_all_logbook_out"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                result = self.logbook_use_case.get_logbooks_out(request.headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Bitacoras de salida obtenidas correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_history_logbook(self):
        internal_process = (None, None)
        function_name = "get_history_logbook"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                result = self.logbook_use_case.get_history_logbooks(request.headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Historial de bitacoras obtenido correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code

    def get_resume_graphs(self):
        internal_process = (None, None)
        function_name = "get_resume_graphs"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                result = self.logbook_use_case.get_resume_graphs(request.headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Datos obtenidos correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
