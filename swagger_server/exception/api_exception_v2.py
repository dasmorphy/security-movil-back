import sys
import traceback
from typing import Optional

from swagger_server.models import ResponseError


class CustomAPIExceptionV2(Exception):

    def __init__(self, error_code: int, error_reason: str, message: str, status_code: int, data: dict = None):
        self.status_code = status_code
        self.data = data
        self.error_code = error_code
        self.error_reason = error_reason

        super().__init__(message)

    @staticmethod
    def check_exception(error, internal_transaction_id, external_transaction_id, data_log):
        log = data_log["log"]
        function_name = data_log["function_name"]
        package_name = data_log["package_name"]

        msg_error: str = str(error)
        line: Optional[int]
        _, _, exc_traceback = sys.exc_info()
        traceback_info = traceback.extract_tb(exc_traceback)

        # Retrieve the module or class name where the exception originated
        if traceback_info:
            package_name = traceback_info[-1][0]  # Get the last item in the traceback
            i_package_name: int = package_name.find('-ms\\')
            package_name = package_name[i_package_name + 4 if i_package_name != 0 else None:].replace('\\', '.')
            package_name = package_name.replace('.py', '')
            line = traceback_info[-1][1]
            function_name = traceback_info[-1][2]

        status_code = 500
        response = ResponseError(
            error_code=-1, message='Hubo un error al procesar la petición'
        )
        try:
            response.internal_transaction_id = internal_transaction_id
            response.external_transaction_id = external_transaction_id
            if isinstance(error, CustomAPIExceptionV2):  # Es un error esperado, para notificar error al cliente
                status_code = error.status_code
                message = str(error)
                response.message = message
                response.reason = error.error_reason
                response.code = error.error_code
            else:  # En caso no sea un error custom, se agrega la línea para validar donde ocurrió el error no esperado
                if line: msg_error = f'{msg_error} in line: {line}'

            log.error(internal_transaction_id, external_transaction_id, function_name, package_name, msg_error)
        except Exception as e:
            print('check_exception', internal_transaction_id, external_transaction_id, log, str(e))
            # pass
        return response, status_code
