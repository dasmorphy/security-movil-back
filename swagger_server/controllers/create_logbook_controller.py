import connexion
import six

from flask.views import MethodView

from swagger_server.models.request_post_logbook_entry import RequestPostLogbookEntry  # noqa: E501
from swagger_server.models.request_post_logbook_out import RequestPostLogbookOut  # noqa: E501
from swagger_server.models.response_error import ResponseError  # noqa: E501
from swagger_server.models.response_post_logbook_entry import ResponsePostLogbookEntry  # noqa: E501
from swagger_server.models.response_post_logbook_out import ResponsePostLogbookOut  # noqa: E501
from swagger_server import util
from loguru import logger


class LogbookView(MethodView):
    def __init__(self):
        self.logger = logger
        # contract_limit_repository = ContractLimitRepository(self.logger)
        # self.contract_limit_use_case = ContractLimitUseCase(contract_limit_repository)

    def post_logbook_entry(body=None):  # noqa: E501
        """Guarda la bitacora de ingreso en la base de datos.

        Guardado de bitacora de ingreso # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: ResponsePostLogbookEntry
        """
        if connexion.request.is_json:
            body = RequestPostLogbookEntry.from_dict(connexion.request.get_json())  # noqa: E501
        return 'do some magic!'


    def post_logbook_out(body=None):  # noqa: E501
        """Guarda la bitacora de salida en la base de datos.

        Guardado de bitacora de salida # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: ResponsePostLogbookOut
        """
        if connexion.request.is_json:
            body = RequestPostLogbookOut.from_dict(connexion.request.get_json())  # noqa: E501
        return 'do some magic!'
