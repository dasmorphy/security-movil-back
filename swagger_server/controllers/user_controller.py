


from timeit import default_timer
import connexion
from flask.views import MethodView
from loguru import logger

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.request_login import RequestLogin
from swagger_server.models.request_post_new_user import RequestPostNewUser
from swagger_server.repository.user_repository import UserRepository
from swagger_server.uses_cases.user_use_case import UserUseCase
from swagger_server.utils.transactions.transaction import generate_internal_transaction_id


class UserView(MethodView):
    def __init__(self):
        self.logger = logger
        user_repository = UserRepository()
        self.user_use_case = UserUseCase(user_repository)


    def get_all_users(self, body=None):  # noqa: E501
        """Guarda el usuario de ingreso en la base de datos.

        Guardado de usuario # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: ResponseGeneric
        """
        internal_process = (None, None)
        function_name = "get_all_users"
        response = {}
        status_code = 500
        try:
            if connexion.request.is_json:
                body = RequestPostNewUser.from_dict(connexion.request.get_json())  # noqa: E501
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = body.external_transaction_id
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {body.channel}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                self.user_use_case.post_new_user(body, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Usuario creado correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=body.external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def login(self, body=None):  # noqa: E501
        """Guarda el usuario de ingreso en la base de datos.

        Guardado de usuario # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: ResponseGeneric
        """
        internal_process = (None, None)
        function_name = "login"
        response = {}
        status_code = 500
        try:
            if connexion.request.is_json:
                body = RequestLogin.from_dict(connexion.request.get_json())  # noqa: E501
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = body.external_transaction_id
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {body.channel}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                user = self.user_use_case.login(body, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Login correcto",
                response["data"] = user
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=body.external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code

    def new_user(self, body=None):  # noqa: E501
        """Guarda el usuario de ingreso en la base de datos.

        Guardado de usuario # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: ResponseGeneric
        """
        internal_process = (None, None)
        function_name = "new_user"
        response = {}
        status_code = 500
        try:
            if connexion.request.is_json:
                body = RequestPostNewUser.from_dict(connexion.request.get_json())  # noqa: E501
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = body.external_transaction_id
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {body.channel}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                self.user_use_case.post_new_user(body, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Usuario creado correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=body.external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code