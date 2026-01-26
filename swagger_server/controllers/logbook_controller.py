from json import JSONEncoder
from timeit import default_timer
import connexion
from flask import jsonify, request
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

        :rtype: ResponsePostLogbookOut
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
