    
from timeit import default_timer
from loguru import logger

import connexion
from flask import json, request
from flask.views import MethodView

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.request_post_employee_movement import RequestPostEmployeeMovement
from swagger_server.models.request_update_status_employee import RequestUpdateStatusEmployee
from swagger_server.repository.employee_repository import EmployeeRepository
from swagger_server.repository.logbook_repository import LogbookRepository
from swagger_server.uses_cases.employee_use_case import EmployeeUseCase
from swagger_server.uses_cases.logbook_use_case import LogbookUseCase
from swagger_server.utils.transactions.transaction import generate_internal_transaction_id


class EmployeeView(MethodView):
    def __init__(self):
        self.logger = logger
        employee_repository = EmployeeRepository()
        self.employee_use_case = EmployeeUseCase(employee_repository)

    def post_employee_intern(self):
        internal_process = (None, None)
        function_name = "post_employee_intern"
        response = {}
        status_code = 500
        try:
            if request.content_type.startswith("multipart/form-data"):
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())

                employee_file = request.files.get("employee_data")
                if not employee_file:
                    raise CustomAPIException("Campo employee_data no enviado", 400)

                employee_raw = employee_file.read().decode("utf-8")
                employee_dict = json.loads(employee_raw)

                external_transaction_id = employee_dict['external_transaction_id']
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {employee_dict['channel']}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                files = request.files.getlist("images")
                self.employee_use_case.post_employee_intern(employee_dict, files, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Personal creado correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    

    def get_employees_intern(self):
        internal_process = (None, None)
        function_name = "get_employees_intern"
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
                headers = {k.lower(): v for k, v in request.headers.items()}
                results = self.employee_use_case.get_employees_intern(headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Personal obtenido correctamente"
                response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    

    def post_employee_movement(self):
        internal_process = (None, None)
        function_name = "post_employee_movement"
        response = {}
        status_code = 500
        try:
            if request.content_type.startswith("multipart/form-data"):
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())

                movement_file = request.files.get("employee_movement")
                if not movement_file:
                    raise CustomAPIException("Campo employee_movement no enviado", 400)

                movement_raw = movement_file.read().decode("utf-8")
                movement_dict = json.loads(movement_raw)

                external_transaction_id = movement_dict['external_transaction_id']
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {movement_dict['channel']}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                files = request.files.getlist("images")
                self.employee_use_case.post_employee_movement(movement_dict, files, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Movimiento de personal creado correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    

    def get_employees_movement(self):
        internal_process = (None, None)
        function_name = "get_employees_movement"
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
                headers = {k.lower(): v for k, v in request.headers.items()}
                results = self.employee_use_case.get_employees_movement(headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Movimientos de personal obtenidos correctamente"
                response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code

    def update_status_employee(self, id_employee_intern):
        internal_process = (None, None)
        function_name = "update_status_employee"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                body = RequestUpdateStatusEmployee.from_dict(connexion.request.get_json())  # noqa: E501
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, employee_id: {id_employee_intern}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)                
                self.employee_use_case.update_employee_intern_status(id_employee_intern, body.data, internal_process)
                response["error_code"] = 0
                response["message"] = "Estado del personal actualizado correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def resume_graphs_employees(self):
        internal_process = (None, None)
        function_name = "resume_graphs_employees"
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
                headers = {k.lower(): v for k, v in request.headers.items()}
                result = self.employee_use_case.get_resume_graphs(headers, request.args, internal_transaction_id, external_transaction_id)
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